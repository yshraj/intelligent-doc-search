# Document Grouper - Features & Usage

## Overview

The Document Grouper automatically classifies, tags, and organizes documents in LiveDocAI. It analyzes document content during upload and assigns relevant tags and group memberships.

## Features

### 1. Automatic Document Classification

**What it does:**
- Detects document type (contract, report, memo, policy, invoice, etc.)
- Identifies topics (legal, finance, technical, hr, marketing, operations)
- Determines sensitivity level (public, internal, confidential, anonymous)
- Extracts time periods from filenames and content
- Detects anonymous documents (missing metadata)

**How it works:**
- Pattern matching using regex (< 100ms)
- Optional LLM enhancement using Gemini (1-3 seconds)
- Confidence scores for each tag (0.0 to 1.0)
- Multi-label classification (multiple tags per document)

**Example:**
```
Upload: "Service_Agreement_2024.pdf"

Auto-generated tags:
- contract (type, confidence: 0.95)
- legal (topic, confidence: 0.85)
- confidential (sensitivity, confidence: 0.9)
- FY2024 (time_period, confidence: 0.8)

Auto-created groups:
- Contracts
- Legal Documents
- FY2024
```

### 2. Hierarchical Document Groups

**What it does:**
- Organizes documents into logical groups
- Supports parent-child relationships
- Auto-creates groups based on tags
- Allows custom group creation

**Group Types:**
- `type_based` - By document type (Contracts, Reports, etc.)
- `topic_based` - By topic (Legal Documents, Financial Documents, etc.)
- `time_based` - By time period (Q1 2024, FY2024, etc.)
- `department_based` - By department (Engineering, Sales, etc.)
- `custom` - User-defined groups

**Example Hierarchy:**
```
Legal Documents (parent)
├── Contracts (child)
│   ├── Vendor Contracts (grandchild)
│   └── Customer Contracts (grandchild)
└── Policies (child)
```

### 3. Tag Management

**What it does:**
- View all tags for a document
- Add custom tags manually
- Remove unwanted tags
- Search documents by tags
- Filter by tag category

**Tag Categories:**
- **type** - Document types
- **topic** - Subject areas
- **department** - Organizational units
- **sensitivity** - Access levels
- **time_period** - Temporal grouping
- **status** - Document state
- **custom** - User-defined

**UI Features:**
- Color-coded badges by category
- Confidence score indicators
- Auto-generated vs manual tags
- Bulk tag operations

### 4. Document Search & Filter

**What it does:**
- Search documents by multiple tags
- Filter by group
- Filter by tag category
- Filter by sensitivity level
- Filter by time period

**Search Examples:**
```
# Find all contracts
tag_names=contract

# Find legal contracts
tag_names=contract,legal

# Find Q1 2024 reports
tag_names=report,Q1_2024

# Find confidential documents
tag_names=confidential
```

### 5. Document Organization UI

**Components:**

**A. Document Organization Panel**
- Tree view of groups and categories
- Document count badges
- Expand/collapse groups
- Drag-and-drop support (future)

**B. Tag Manager**
- View document tags
- Add/remove tags
- Tag category selection
- Confidence indicators

**C. Group Manager**
- Create/delete groups
- Assign documents to groups
- View group documents
- Hierarchical display

**D. Sensitivity Badge**
- Visual indicators for sensitivity levels
- Color-coded (green=public, yellow=internal, red=confidential, gray=anonymous)
- Tooltip with details

---

## Usage Examples

### Example 1: Organize Legal Documents

**Scenario:** Upload contracts and policies

**What happens:**
1. Upload "Vendor_Service_Agreement_2024.pdf"
2. System detects: type=contract, topic=legal, sensitivity=confidential
3. Groups created: "Contracts", "Legal Documents"
4. Document assigned to both groups
5. Searchable by tags: contract, legal, confidential

**Result:** All legal documents automatically organized and searchable

### Example 2: Track Financial Reports

**Scenario:** Upload quarterly financial reports

**What happens:**
1. Upload "Q1_2024_Financial_Report.pdf"
2. System detects: type=report, topic=finance, time_period=Q1_2024
3. Groups created: "Reports", "Financial Documents", "Q1 2024"
4. Document assigned to all three groups
5. Searchable by tags: report, finance, Q1_2024

**Result:** Financial reports organized by time period and topic

### Example 3: Archive Meeting Notes

**Scenario:** Upload team meeting minutes

**What happens:**
1. Upload "Team_Meeting_2024-03-15.txt"
2. System detects: type=meeting_notes
3. Group created: "Meeting Notes"
4. Document assigned to group
5. Searchable by tags: meeting_notes

**Result:** Meeting notes organized and easily accessible

### Example 4: Manage Confidential Documents

**Scenario:** Upload documents with confidential markers

**What happens:**
1. Upload "Strategy_2024_CONFIDENTIAL.pdf"
2. System detects: sensitivity=confidential
3. Red badge displayed in UI
4. Filterable by sensitivity level
5. Access control ready (future feature)

**Result:** Confidential documents flagged and easily identifiable

### Example 5: Find Anonymous Documents

**Scenario:** Upload documents without metadata

**What happens:**
1. Upload "untitled.txt" with no author/date
2. System detects: sensitivity=anonymous
3. Gray badge displayed in UI
4. Flagged for manual review
5. User can add proper tags manually

**Result:** Documents needing attention are identified

---

## Pattern Matching Details

### Contract Detection

**Patterns:**
- "agreement", "contract", "terms and conditions"
- "party", "parties", "whereas", "hereby"
- "effective date", "termination", "renewal"
- "liability", "indemnity", "jurisdiction"

**Example:**
```
"This Agreement is entered into by Party A and Party B.
WHEREAS, the parties wish to establish terms...
LIABILITY: Each party shall indemnify the other."

Detected: type=contract, topic=legal
```

### Report Detection

**Patterns:**
- "executive summary", "findings", "recommendations"
- "analysis", "results", "data", "metrics"
- "quarterly report", "annual report", "monthly report"

**Example:**
```
"QUARTERLY FINANCIAL REPORT
EXECUTIVE SUMMARY
Revenue increased by 15%...
ANALYSIS: Strong performance..."

Detected: type=report, topic=finance, time_period=Q1_2024
```

### Meeting Notes Detection

**Patterns:**
- "meeting", "minutes", "attendees", "agenda"
- "action items", "next steps", "follow-up"
- "discussed", "decided", "agreed"

**Example:**
```
"MEETING MINUTES
ATTENDEES: John, Jane
AGENDA: Project update
ACTION ITEMS: Complete by Friday"

Detected: type=meeting_notes
```

### Sensitivity Detection

**Patterns:**
- **Confidential:** "confidential", "proprietary", "restricted", "private"
- **Public:** "public", "published", "press release"
- **Internal:** Default if no explicit marker

**Example:**
```
"CONFIDENTIAL - INTERNAL USE ONLY
This document contains proprietary information."

Detected: sensitivity=confidential
```

### Time Period Detection

**Patterns:**
- Year: "2024", "FY2024"
- Quarter: "Q1 2024", "Q1_2024"
- Month: "January 2024", "Jan 2024"

**Example:**
```
Filename: "Q1_2024_Report.pdf"
Content: "First quarter of 2024..."

Detected: time_period=Q1_2024
```

---

## UI Components

### 1. Document Organization Panel

**Location:** Main dashboard sidebar

**Features:**
- Tree view of groups
- Document count badges
- Filter by group
- Search within group
- Expand/collapse

**Usage:**
```jsx
<DocumentOrganization 
  userId={user.id}
  onDocumentSelect={(doc) => console.log(doc)}
/>
```

### 2. Tag Manager

**Location:** Document detail view

**Features:**
- List all tags
- Add custom tags
- Remove tags
- Tag category badges
- Confidence indicators

**Usage:**
```jsx
<TagManager 
  documentId={doc.id}
  onTagsChange={(tags) => console.log(tags)}
/>
```

### 3. Group Manager

**Location:** Settings or admin panel

**Features:**
- Create groups
- Delete groups
- Assign documents
- View group documents
- Hierarchical display

**Usage:**
```jsx
<GroupManager 
  userId={user.id}
  onGroupChange={(groups) => console.log(groups)}
/>
```

### 4. Sensitivity Badge

**Location:** Document list items

**Features:**
- Color-coded badges
- Tooltip with details
- Click to filter

**Usage:**
```jsx
<SensitivityBadge 
  level="confidential"
  onClick={() => filterBySensitivity('confidential')}
/>
```

---

## Performance

| Operation | Time |
|-----------|------|
| Pattern matching | < 100ms |
| LLM classification (optional) | 1-3 seconds |
| Tag creation | < 50ms |
| Group creation | < 50ms |
| Search by tags | < 100ms |
| Full document processing | 2-5 seconds |

---

## Security

- **Row Level Security (RLS)** - Users can only access their own documents, tags, and groups
- **JWT Authentication** - All API requests require valid token
- **Permission Inheritance** - Tags and groups inherit document permissions
- **Automatic Filtering** - Database-level filtering by user_id

---

## Customization

### Add Custom Patterns

Edit `backend/app/document_grouper.py`:

```python
TYPE_PATTERNS = {
    "contract": [...],
    "report": [...],
    # Add your custom type
    "invoice": [
        r"\b(invoice|bill|payment)\b",
        r"\b(amount|total|due date)\b",
    ],
}
```

### Add Custom Tag Categories

Edit database schema:

```sql
ALTER TABLE document_tags 
DROP CONSTRAINT document_tags_tag_category_check;

ALTER TABLE document_tags 
ADD CONSTRAINT document_tags_tag_category_check 
CHECK (tag_category IN ('type', 'topic', 'department', 'sensitivity', 'time_period', 'status', 'custom', 'your_category'));
```

### Add Custom Groups

Via API:

```bash
curl -X POST http://localhost:8000/groups \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "group_name": "Your Custom Group",
    "group_type": "custom",
    "description": "Description here"
  }'
```

---

## Future Enhancements

- [ ] Bulk tag operations
- [ ] Tag suggestions based on similar documents
- [ ] Group templates for common structures
- [ ] Export tagged document lists
- [ ] Analytics dashboard for tag usage
- [ ] Machine learning model training on user corrections
- [ ] Automatic re-classification when patterns change
- [ ] Drag-and-drop document organization
- [ ] Collaborative tagging
- [ ] Tag hierarchies

---

## API Reference

See `SETUP.md` for detailed API documentation and examples.

---

## Support

For issues or questions:
1. Check `SETUP.md` for setup instructions
2. Review `DEVELOPMENT.md` for architecture details
3. Run tests: `python3 backend/test_grouper_simple.py`
4. Check backend logs for errors
