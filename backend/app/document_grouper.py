"""Document grouping and tagging system for automatic organization."""
import logging
import re
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import genai, but make it optional
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not available, LLM classification disabled")

from app.config import settings


class DocumentGrouper:
    """Analyzes documents and assigns tags and groups automatically."""
    
    # Document type patterns
    TYPE_PATTERNS = {
        "contract": [
            r"\b(agreement|contract|terms and conditions|service agreement)\b",
            r"\b(party|parties|whereas|hereby)\b",
            r"\b(effective date|termination|renewal)\b",
        ],
        "report": [
            r"\b(executive summary|findings|recommendations|conclusion)\b",
            r"\b(analysis|results|data|metrics)\b",
            r"\b(quarterly|annual|monthly) report\b",
        ],
        "meeting_notes": [
            r"\b(meeting|minutes|attendees|agenda)\b",
            r"\b(action items|next steps|follow.?up)\b",
            r"\b(discussed|decided|agreed)\b",
        ],
        "policy": [
            r"\b(policy|procedure|guidelines|standards)\b",
            r"\b(compliance|requirements|mandatory)\b",
            r"\b(effective date|revision|version)\b",
        ],
        "invoice": [
            r"\b(invoice|bill|payment|due date)\b",
            r"\b(amount|total|subtotal|tax)\b",
            r"\b(invoice number|invoice date)\b",
        ],
        "memo": [
            r"\b(memorandum|memo|to:|from:|subject:)\b",
            r"\b(internal|confidential|for your information)\b",
        ],
        "proposal": [
            r"\b(proposal|bid|quotation|estimate)\b",
            r"\b(scope of work|deliverables|timeline)\b",
            r"\b(pricing|cost|budget)\b",
        ],
        "presentation": [
            r"\b(slide|presentation|deck)\b",
            r"\b(overview|introduction|summary)\b",
        ],
    }
    
    # Topic patterns
    TOPIC_PATTERNS = {
        "legal": [
            r"\b(legal|law|attorney|counsel|litigation)\b",
            r"\b(clause|liability|indemnity|jurisdiction)\b",
        ],
        "finance": [
            r"\b(financial|budget|revenue|expense|profit)\b",
            r"\b(accounting|fiscal|investment|cost)\b",
        ],
        "hr": [
            r"\b(human resources|employee|personnel|hiring)\b",
            r"\b(benefits|compensation|performance review)\b",
        ],
        "technical": [
            r"\b(technical|software|hardware|system|architecture)\b",
            r"\b(api|database|server|deployment)\b",
        ],
        "marketing": [
            r"\b(marketing|campaign|brand|advertising)\b",
            r"\b(customer|market|promotion|sales)\b",
        ],
        "operations": [
            r"\b(operations|process|workflow|logistics)\b",
            r"\b(supply chain|inventory|production)\b",
        ],
    }
    
    # Sensitivity patterns
    SENSITIVITY_PATTERNS = {
        "confidential": [
            r"\b(confidential|proprietary|restricted|private)\b",
            r"\b(do not distribute|internal only)\b",
        ],
        "public": [
            r"\b(public|published|press release)\b",
        ],
    }
    
    def __init__(self):
        """Initialize the document grouper."""
        self.client = None
        if GENAI_AVAILABLE and settings.gemini_api_key:
            try:
                self.client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as exc:
                logger.warning("Failed to initialize Gemini client: %s", exc)
    
    def analyze_document(
        self,
        content: str,
        filename: str,
        mime_type: str,
    ) -> dict[str, Any]:
        """
        Analyze document and return tags and group suggestions.
        
        Returns:
        {
            "tags": [
                {"name": "contract", "category": "type", "confidence": 0.95},
                {"name": "legal", "category": "topic", "confidence": 0.85},
                ...
            ],
            "suggested_groups": ["Legal Documents", "Contracts"],
            "is_anonymous": bool
        }
        """
        tags = []
        suggested_groups = []
        
        # Analyze content
        content_lower = content.lower()
        
        # 1. Detect document type
        type_tag = self._detect_type(content_lower, filename)
        if type_tag:
            tags.append(type_tag)
            suggested_groups.append(self._type_to_group_name(type_tag["name"]))
        
        # 2. Detect topics
        topic_tags = self._detect_topics(content_lower)
        tags.extend(topic_tags)
        for topic_tag in topic_tags:
            suggested_groups.append(self._topic_to_group_name(topic_tag["name"]))
        
        # 3. Detect sensitivity
        sensitivity_tag = self._detect_sensitivity(content_lower, filename)
        if sensitivity_tag:
            tags.append(sensitivity_tag)
        
        # 4. Detect time period from filename or content
        time_tag = self._detect_time_period(content, filename)
        if time_tag:
            tags.append(time_tag)
            suggested_groups.append(time_tag["name"])
        
        # 5. Check if anonymous (missing metadata)
        is_anonymous = self._is_anonymous(content, filename)
        if is_anonymous:
            tags.append({
                "name": "anonymous",
                "category": "sensitivity",
                "confidence": 1.0,
            })
        
        # 6. Use LLM for enhanced classification if available
        # Disabled by default - pattern matching is sufficient
        # Uncomment below to enable LLM enhancement
        # if self.client and len(content) > 100:
        #     llm_tags = self._llm_classify(content[:3000])
        #     tags.extend(llm_tags)
        
        return {
            "tags": tags,
            "suggested_groups": list(set(suggested_groups)),  # Remove duplicates
            "is_anonymous": is_anonymous,
        }
    
    def _detect_type(self, content: str, filename: str) -> dict[str, Any] | None:
        """Detect document type using pattern matching."""
        scores = {}
        
        for doc_type, patterns in self.TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                score += matches
            
            # Boost score if type is in filename
            if doc_type.replace("_", " ") in filename.lower():
                score += 5
            
            if score > 0:
                scores[doc_type] = score
        
        if not scores:
            return None
        
        # Get type with highest score
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        
        # Calculate confidence (normalize to 0-1)
        confidence = min(0.5 + (max_score * 0.1), 1.0)
        
        return {
            "name": best_type,
            "category": "type",
            "confidence": confidence,
        }
    
    def _detect_topics(self, content: str) -> list[dict[str, Any]]:
        """Detect topics using pattern matching."""
        tags = []
        
        for topic, patterns in self.TOPIC_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                score += matches
            
            if score > 0:
                confidence = min(0.4 + (score * 0.1), 1.0)
                tags.append({
                    "name": topic,
                    "category": "topic",
                    "confidence": confidence,
                })
        
        # Return top 3 topics
        tags.sort(key=lambda x: x["confidence"], reverse=True)
        return tags[:3]
    
    def _detect_sensitivity(self, content: str, filename: str) -> dict[str, Any] | None:
        """Detect document sensitivity level."""
        for level, patterns in self.SENSITIVITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE) or re.search(pattern, filename, re.IGNORECASE):
                    return {
                        "name": level,
                        "category": "sensitivity",
                        "confidence": 0.9,
                    }
        
        # Default to internal if no explicit marker
        return {
            "name": "internal",
            "category": "sensitivity",
            "confidence": 0.5,
        }
    
    def _detect_time_period(self, content: str, filename: str) -> dict[str, Any] | None:
        """Detect time period from filename or content."""
        # Check for year patterns
        year_pattern = r"\b(20\d{2})\b"
        years = re.findall(year_pattern, filename + " " + content[:500])
        
        if years:
            year = years[0]
            return {
                "name": f"FY{year}",
                "category": "time_period",
                "confidence": 0.8,
            }
        
        # Check for quarter patterns
        quarter_pattern = r"\b(Q[1-4])\s*(20\d{2})\b"
        quarters = re.findall(quarter_pattern, filename + " " + content[:500], re.IGNORECASE)
        
        if quarters:
            quarter, year = quarters[0]
            return {
                "name": f"{quarter.upper()}_{year}",
                "category": "time_period",
                "confidence": 0.9,
            }
        
        # Check for month patterns
        month_pattern = r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s*(20\d{2})\b"
        months = re.findall(month_pattern, filename + " " + content[:500], re.IGNORECASE)
        
        if months:
            month, year = months[0]
            return {
                "name": f"{month}_{year}",
                "category": "time_period",
                "confidence": 0.85,
            }
        
        return None
    
    def _is_anonymous(self, content: str, filename: str) -> bool:
        """Check if document lacks identifying metadata."""
        # Check for common metadata indicators
        metadata_patterns = [
            r"\b(author|created by|prepared by)\b",
            r"\b(company|organization|department)\b",
            r"\b(date|version|revision)\b",
        ]
        
        metadata_found = False
        for pattern in metadata_patterns:
            if re.search(pattern, content[:1000], re.IGNORECASE):
                metadata_found = True
                break
        
        # Check if filename is generic
        generic_names = ["untitled", "document", "file", "scan", "temp"]
        is_generic_name = any(name in filename.lower() for name in generic_names)
        
        return not metadata_found or is_generic_name
    
    def _llm_classify(self, content_sample: str) -> list[dict[str, Any]]:
        """Use LLM for enhanced classification."""
        if not self.client:
            return []
        
        try:
            prompt = f"""Analyze this document excerpt and provide classification tags.

Document excerpt:
{content_sample}

Provide tags in these categories:
1. Document type (contract, report, memo, policy, etc.)
2. Topic area (legal, finance, technical, hr, marketing, operations, etc.)
3. Department (if identifiable)

Respond with a JSON array of tags in this format:
[
  {{"name": "contract", "category": "type", "confidence": 0.95}},
  {{"name": "legal", "category": "topic", "confidence": 0.85}}
]

Only include tags you're confident about (confidence > 0.6).
"""
            
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",  # Use stable model instead
                contents=prompt,
            )
            
            # Parse JSON response
            import json
            text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            tags = json.loads(text)
            
            # Validate and filter tags
            valid_tags = []
            for tag in tags:
                if isinstance(tag, dict) and "name" in tag and "category" in tag:
                    if tag.get("confidence", 0) > 0.6:
                        valid_tags.append(tag)
            
            return valid_tags
        
        except Exception as exc:
            logger.warning("LLM classification failed: %s", exc)
            return []
    
    def _type_to_group_name(self, doc_type: str) -> str:
        """Convert document type to group name."""
        type_map = {
            "contract": "Contracts",
            "report": "Reports",
            "meeting_notes": "Meeting Notes",
            "policy": "Policies",
            "invoice": "Invoices",
            "memo": "Memos",
            "proposal": "Proposals",
            "presentation": "Presentations",
        }
        return type_map.get(doc_type, doc_type.replace("_", " ").title())
    
    def _topic_to_group_name(self, topic: str) -> str:
        """Convert topic to group name."""
        topic_map = {
            "legal": "Legal Documents",
            "finance": "Financial Documents",
            "hr": "HR Documents",
            "technical": "Technical Documents",
            "marketing": "Marketing Materials",
            "operations": "Operations Documents",
        }
        return topic_map.get(topic, topic.replace("_", " ").title())
    
    def create_groups_for_user(
        self,
        user_id: str,
        group_names: list[str],
        group_type: str = "type_based",
    ) -> list[str]:
        """
        Create document groups for a user.
        Returns list of created group IDs.
        """
        # This will be called from the API layer with database access
        # Implementation will be in the router
        pass
    
    def assign_document_to_groups(
        self,
        document_id: str,
        group_ids: list[str],
    ) -> None:
        """
        Assign a document to multiple groups.
        Implementation will be in the router.
        """
        pass


# Global instance
document_grouper = DocumentGrouper()
