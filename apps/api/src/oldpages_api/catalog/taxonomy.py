"""The book category tree shown in the Sell form and search filters.

Each node's slug is its parent's slug plus its own part ("academic.school.cbse.class-10"), so
a filter on any node can match everything below it with a prefix. `child_label` names the
next dropdown ("Board", "Class", "Subject"). Edit this file, then run
`python -m oldpages_api.scripts.sync_categories` (or migrate) to apply it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    name: str
    children: tuple[Node, ...] = ()
    child_label: str | None = None
    part: str | None = None  # slug part; derived from the name when omitted

    @property
    def slug_part(self) -> str:
        return self.part or slugify(self.name)


@dataclass(frozen=True)
class FlatCategory:
    slug: str
    name: str
    parent_slug: str | None
    child_label: str | None
    sort_order: int
    depth: int = field(default=0)


def slugify(value: str) -> str:
    value = value.lower().replace("&", "and").replace("+", "plus")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def n(name: str, *children: Node | str, label: str | None = None, part: str | None = None) -> Node:
    kids = tuple(c if isinstance(c, Node) else Node(c) for c in children)
    return Node(name=name, children=kids, child_label=label if kids else None, part=part)


def leaves(*names: str) -> tuple[Node, ...]:
    return tuple(Node(name) for name in names)


# ---------------------------------------------------------------------------
# Academic: school (board -> class -> subject) and college (stream -> course -> subject)
# ---------------------------------------------------------------------------

_PRE_PRIMARY = leaves(
    "English", "Mathematics", "EVS", "Hindi", "Rhymes & Stories", "Drawing & Colouring"
)
_PRIMARY = leaves(
    "English",
    "Hindi",
    "Mathematics",
    "EVS",
    "Regional Language",
    "Computer Science",
    "General Knowledge",
    "Drawing & Art",
)
_MIDDLE = leaves(
    "English",
    "Hindi",
    "Mathematics",
    "Science",
    "Social Science",
    "Sanskrit",
    "Regional Language",
    "Computer Science",
    "General Knowledge",
)
_SECONDARY = leaves(
    "English",
    "Hindi",
    "Mathematics",
    "Science",
    "Social Science",
    "Sanskrit",
    "Regional Language",
    "Computer / IT",
)
_SENIOR = leaves(
    "Physics",
    "Chemistry",
    "Mathematics",
    "Biology",
    "Computer Science",
    "Informatics Practices",
    "English",
    "Hindi",
    "Accountancy",
    "Business Studies",
    "Economics",
    "History",
    "Political Science",
    "Geography",
    "Psychology",
    "Sociology",
    "Physical Education",
)


def _classes() -> tuple[Node, ...]:
    pre = tuple(n(name, *_PRE_PRIMARY, label="Subject") for name in ("Nursery", "LKG", "UKG"))

    def band(k: int) -> tuple[Node, ...]:
        if k <= 5:
            return _PRIMARY
        if k <= 8:
            return _MIDDLE
        if k <= 10:
            return _SECONDARY
        return _SENIOR

    graded = tuple(n(f"Class {k}", *band(k), label="Subject") for k in range(1, 13))
    return pre + graded


_BOARDS = ("CBSE", "ICSE / ISC", "State Board", "NIOS", "IB", "Cambridge (IGCSE / A Level)")

SCHOOL = n(
    "School Books",
    *(n(board, *_classes(), label="Class / Grade") for board in _BOARDS),
    label="Board",
    part="school",
)

_ENGG_FIRST_YEAR = leaves(
    "Engineering Mathematics",
    "Engineering Physics",
    "Engineering Chemistry",
    "Programming in C",
    "Engineering Graphics",
    "Basic Electrical Engineering",
    "Basic Electronics",
    "Engineering Mechanics",
    "Communication English",
)

COLLEGE = n(
    "College & University",
    n(
        "Engineering",
        n("First Year (Common)", *_ENGG_FIRST_YEAR, label="Subject"),
        n(
            "Computer Science (CSE)",
            "Data Structures",
            "Algorithms",
            "Discrete Mathematics",
            "Computer Organisation",
            "Operating Systems",
            "Database Systems (DBMS)",
            "Computer Networks",
            "Theory of Computation",
            "Compiler Design",
            "Software Engineering",
            "Artificial Intelligence",
            "Machine Learning",
            "Web Technologies",
            "Cloud Computing",
            "Cyber Security",
            label="Subject",
        ),
        n(
            "Information Technology",
            "Data Structures",
            "Database Systems (DBMS)",
            "Computer Networks",
            "Operating Systems",
            "Web Technologies",
            "Software Engineering",
            "Cyber Security",
            label="Subject",
        ),
        n(
            "AI & Data Science",
            "Python Programming",
            "Statistics & Probability",
            "Machine Learning",
            "Deep Learning",
            "Data Mining",
            "Big Data Analytics",
            "Natural Language Processing",
            label="Subject",
        ),
        n(
            "Electronics & Communication (ECE)",
            "Electronic Devices & Circuits",
            "Network Theory",
            "Signals & Systems",
            "Digital Electronics",
            "Analog Communication",
            "Digital Communication",
            "Microprocessors & Microcontrollers",
            "Control Systems",
            "VLSI Design",
            "Electromagnetic Theory",
            "Embedded Systems",
            label="Subject",
        ),
        n(
            "Electrical & Electronics (EEE)",
            "Electrical Circuits",
            "Electrical Machines",
            "Power Systems",
            "Power Electronics",
            "Control Systems",
            "Measurements & Instrumentation",
            "Electromagnetic Fields",
            label="Subject",
        ),
        n(
            "Mechanical",
            "Engineering Mechanics",
            "Thermodynamics",
            "Fluid Mechanics",
            "Strength of Materials",
            "Theory of Machines",
            "Machine Design",
            "Manufacturing Processes",
            "Heat & Mass Transfer",
            "CAD / CAM",
            label="Subject",
        ),
        n(
            "Civil",
            "Surveying",
            "Strength of Materials",
            "Structural Analysis",
            "Concrete Technology",
            "Geotechnical Engineering",
            "Transportation Engineering",
            "Environmental Engineering",
            "Hydraulics",
            "Building Materials",
            label="Subject",
        ),
        n(
            "Chemical",
            "Chemical Process Calculations",
            "Mass Transfer",
            "Heat Transfer",
            "Chemical Reaction Engineering",
            "Process Control",
            "Thermodynamics",
            label="Subject",
        ),
        "Aeronautical / Aerospace",
        "Automobile",
        "Biotechnology",
        "Mechatronics",
        "Metallurgy",
        label="Department",
    ),
    n(
        "Medical",
        n(
            "MBBS",
            "Anatomy",
            "Physiology",
            "Biochemistry",
            "Pathology",
            "Pharmacology",
            "Microbiology",
            "Forensic Medicine",
            "Community Medicine",
            "ENT",
            "Ophthalmology",
            "General Medicine",
            "General Surgery",
            "Obstetrics & Gynaecology",
            "Paediatrics",
            "Orthopaedics",
            "Dermatology",
            "Psychiatry",
            label="Subject",
        ),
        n(
            "BDS (Dental)",
            "Dental Anatomy",
            "Oral Pathology",
            "Prosthodontics",
            "Orthodontics",
            "Periodontics",
            "Conservative Dentistry",
            "Oral Surgery",
            label="Subject",
        ),
        "BAMS (Ayurveda)",
        "BHMS (Homeopathy)",
        "Physiotherapy",
        "Allied Health Sciences",
        label="Course",
    ),
    n(
        "Nursing",
        "Anatomy & Physiology",
        "Fundamentals of Nursing",
        "Medical-Surgical Nursing",
        "Community Health Nursing",
        "Child Health Nursing",
        "Mental Health Nursing",
        "Midwifery & Obstetric Nursing",
        "Nutrition",
        label="Subject",
    ),
    n(
        "Pharmacy",
        "Pharmaceutics",
        "Pharmaceutical Chemistry",
        "Pharmacology",
        "Pharmacognosy",
        "Pharmaceutical Analysis",
        "Biopharmaceutics",
        label="Subject",
    ),
    n(
        "Science",
        n(
            "Physics",
            "Mechanics",
            "Electromagnetism",
            "Optics",
            "Quantum Mechanics",
            "Thermal Physics",
            "Solid State Physics",
            "Nuclear Physics",
            label="Subject",
        ),
        n(
            "Chemistry",
            "Organic Chemistry",
            "Inorganic Chemistry",
            "Physical Chemistry",
            "Analytical Chemistry",
            label="Subject",
        ),
        n(
            "Mathematics",
            "Calculus",
            "Linear Algebra",
            "Real Analysis",
            "Abstract Algebra",
            "Differential Equations",
            "Numerical Methods",
            "Statistics",
            label="Subject",
        ),
        "Botany",
        "Zoology",
        "Microbiology",
        "Biotechnology",
        "Biochemistry",
        "Statistics",
        "Electronics",
        "Computer Science",
        "Environmental Science",
        "Geology",
        label="Department",
    ),
    n(
        "Commerce",
        n(
            "B.Com",
            "Financial Accounting",
            "Corporate Accounting",
            "Cost Accounting",
            "Business Law",
            "Income Tax",
            "Auditing",
            "Business Economics",
            "Banking",
            label="Subject",
        ),
        "Accounting & Finance",
        "Banking & Insurance",
        label="Course",
    ),
    n(
        "Management",
        n(
            "BBA",
            "Principles of Management",
            "Marketing Management",
            "Financial Management",
            "Human Resource Management",
            "Organisational Behaviour",
            "Business Statistics",
            label="Subject",
        ),
        n(
            "MBA",
            "Marketing",
            "Finance",
            "Human Resources",
            "Operations",
            "Strategy",
            "Business Analytics",
            "Entrepreneurship",
            label="Subject",
        ),
        label="Course",
    ),
    n(
        "Arts & Humanities",
        "English Literature",
        "History",
        "Political Science",
        "Economics",
        "Sociology",
        "Psychology",
        "Philosophy",
        "Geography",
        "Public Administration",
        "Journalism & Mass Communication",
        "Languages",
        label="Department",
    ),
    n(
        "Law",
        "Constitutional Law",
        "Contract Law",
        "Criminal Law (IPC / BNS)",
        "Civil Procedure",
        "Family Law",
        "Property Law",
        "Jurisprudence",
        "Company Law",
        "Evidence Law",
        "International Law",
        label="Subject",
    ),
    n(
        "Computer Applications",
        n(
            "BCA",
            "Programming in C",
            "Java",
            "Python",
            "Data Structures",
            "DBMS",
            "Web Development",
            "Operating Systems",
            label="Subject",
        ),
        n(
            "MCA",
            "Advanced Java",
            "Data Structures & Algorithms",
            "Software Engineering",
            "Computer Networks",
            "Machine Learning",
            label="Subject",
        ),
        label="Course",
    ),
    "Architecture",
    "Education (B.Ed / D.El.Ed)",
    "Agriculture",
    "Hotel Management",
    "Fashion & Design",
    "Polytechnic / Diploma",
    label="Stream",
    part="college",
)

ACADEMIC = n(
    "Academic & Educational",
    SCHOOL,
    COLLEGE,
    "Reference Books",
    "Laboratory Manuals",
    "Workbooks & Practice",
    "Research & Theses",
    "Academic Journals",
    "Dictionaries & Encyclopedias",
    label="Type",
    part="academic",
)

COMPETITIVE = n(
    "Competitive Exams",
    n("Civil Services", "UPSC CSE", "State PSC", "UPSC CAPF", "UPSC ESE / IES", label="Exam"),
    n(
        "Government Jobs",
        "SSC",
        "Banking (IBPS / SBI)",
        "Railways (RRB)",
        "Defence (NDA / CDS / AFCAT)",
        "Police",
        "Teaching (CTET / TET)",
        "Insurance (LIC / NIACL)",
        label="Exam",
    ),
    n(
        "Engineering Entrance",
        "JEE Main",
        "JEE Advanced",
        "BITSAT",
        "State CETs (EAMCET, MHT-CET...)",
        "GATE",
        label="Exam",
    ),
    n("Medical Entrance", "NEET UG", "NEET PG", "AIIMS / INI-CET", label="Exam"),
    n("Other Entrance", "CUET", "CAT", "CLAT", "NIFT / NID", "IPMAT", "XAT / MAT", label="Exam"),
    n(
        "Study Abroad",
        "GRE",
        "GMAT",
        "SAT",
        "ACT",
        "IELTS",
        "TOEFL",
        "PTE",
        "Duolingo English Test",
        label="Exam",
    ),
    n("Professional", "CA", "CS", "CMA", "ACCA", "CFA", "CPA", "PMP", label="Exam"),
    "General Knowledge & Current Affairs",
    "Aptitude & Reasoning",
    "Previous Year Papers",
    label="Exam group",
    part="competitive-exams",
)


def _section(name: str, part: str, *children: str, label: str = "Genre") -> Node:
    return n(name, *children, label=label, part=part)


TAXONOMY: tuple[Node, ...] = (
    ACADEMIC,
    COMPETITIVE,
    _section(
        "Fiction & Literature",
        "fiction",
        "Literary Fiction",
        "Classics",
        "Contemporary Fiction",
        "Historical Fiction",
        "Short Stories",
        "Anthologies",
        "Indian Writing",
        "Regional Literature",
        "Translated Fiction",
        "World Literature",
        "Satire",
        "Social & Political Fiction",
    ),
    _section(
        "Romance",
        "romance",
        "Contemporary Romance",
        "Historical Romance",
        "Romantic Comedy",
        "Young Adult Romance",
        "Paranormal & Fantasy Romance",
        "Romantic Suspense",
        "College Romance",
        "LGBTQ+ Romance",
    ),
    _section(
        "Mystery, Crime & Thriller",
        "mystery-thriller",
        "Detective & Murder Mystery",
        "Crime Fiction",
        "Psychological Thriller",
        "Legal Thriller",
        "Political & Spy Thriller",
        "Cozy Mystery",
        "True Crime",
        "Suspense",
    ),
    _section(
        "Horror",
        "horror",
        "Supernatural Horror",
        "Psychological Horror",
        "Gothic Horror",
        "Ghost Stories",
        "Vampires & Werewolves",
        "Zombies & Apocalypse",
        "Folk Horror",
        "Horror Anthologies",
    ),
    _section(
        "Fantasy & Science Fiction",
        "fantasy-scifi",
        "Epic & High Fantasy",
        "Urban Fantasy",
        "Dark Fantasy",
        "Mythological Fiction",
        "Magical Realism",
        "Science Fiction",
        "Space Opera",
        "Dystopian",
        "Cyberpunk",
        "Time Travel",
        "Adventure",
    ),
    _section(
        "Children's Books",
        "children",
        "Baby & Toddler",
        "Picture Books",
        "Bedtime & Moral Stories",
        "Fairy Tales & Folk Tales",
        "Early Learning",
        "Activity & Colouring",
        "Children's Fiction",
        "Children's Non-fiction",
        "Children's Comics",
        "Children's Poetry",
    ),
    _section(
        "Young Adult",
        "young-adult",
        "YA Fiction",
        "YA Fantasy",
        "YA Romance",
        "YA Mystery & Thriller",
        "YA Science Fiction",
        "Coming of Age",
        "YA Non-fiction",
    ),
    _section(
        "Comics, Manga & Graphic Novels",
        "comics-manga",
        "Manga",
        "Manhwa & Webtoons",
        "Manhua",
        "Superhero Comics",
        "Indian Comics",
        "Graphic Novels",
        "Comic Strips",
    ),
    _section(
        "Biography & Memoir",
        "biography",
        "Autobiographies",
        "Memoirs",
        "Political Leaders",
        "Scientists",
        "Entrepreneurs",
        "Sports Personalities",
        "Artists & Entertainers",
        "Historical Figures",
        "Inspirational Stories",
        label="Type",
    ),
    _section(
        "Business, Finance & Economics",
        "business",
        "Entrepreneurship & Startups",
        "Management & Leadership",
        "Marketing & Sales",
        "Accounting",
        "Economics",
        "Personal Finance",
        "Investing & Stock Market",
        "Banking",
        "Real Estate",
        "Business Strategy",
        label="Topic",
    ),
    _section(
        "Self-Help & Personal Growth",
        "self-help",
        "Motivation",
        "Productivity & Habits",
        "Communication Skills",
        "Emotional Intelligence",
        "Mindfulness",
        "Relationships",
        "Career Development",
        "Success & Achievement",
        label="Topic",
    ),
    _section(
        "Health, Fitness & Wellbeing",
        "health",
        "General Health",
        "Mental Health",
        "Nutrition & Diet",
        "Fitness",
        "Yoga & Meditation",
        "Pregnancy & Parenting",
        "Alternative Medicine",
        "First Aid",
        label="Topic",
    ),
    _section(
        "Science & Technology",
        "science-tech",
        "Popular Science",
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "Astronomy & Space",
        "Environment",
        "Programming",
        "Artificial Intelligence",
        "Data Science",
        "Cybersecurity",
        "Electronics & Robotics",
        "Engineering",
        label="Topic",
    ),
    _section(
        "History, Politics & Society",
        "history-politics",
        "Indian History",
        "World History",
        "Ancient & Medieval History",
        "Modern History",
        "Military History & Wars",
        "Politics & Government",
        "International Relations",
        "Geography & Atlases",
        "Sociology & Anthropology",
        "Archaeology",
        label="Topic",
    ),
    _section(
        "Religion, Spirituality & Philosophy",
        "religion-philosophy",
        "Hinduism",
        "Islam",
        "Christianity",
        "Buddhism",
        "Sikhism",
        "Jainism",
        "Other Religions",
        "Scriptures",
        "Mythology",
        "Spirituality",
        "Philosophy",
        "Ethics",
        label="Topic",
    ),
    _section(
        "Arts, Music & Design",
        "arts-design",
        "Drawing & Painting",
        "Graphic Design",
        "Fashion Design",
        "Interior Design",
        "Architecture",
        "Photography",
        "Art History",
        "Music",
        "Film & Cinema",
        "Theatre & Dance",
        "Crafts & Calligraphy",
        label="Topic",
    ),
    _section(
        "Languages & Writing",
        "languages",
        "English Grammar & Vocabulary",
        "Hindi",
        "Indian Languages",
        "Foreign Languages",
        "Dictionaries",
        "Linguistics",
        "Creative Writing",
        "Literary Criticism",
        label="Topic",
    ),
    _section(
        "Poetry & Drama",
        "poetry-drama",
        "Classical Poetry",
        "Modern Poetry",
        "Urdu Poetry & Shayari",
        "Epic Poetry",
        "Plays & Scripts",
        "Screenwriting",
    ),
    _section(
        "Lifestyle, Home & Hobbies",
        "lifestyle",
        "Cooking & Recipes",
        "Gardening",
        "Home & Interiors",
        "Travel Guides",
        "Sports",
        "Pets & Animals",
        "Fashion & Beauty",
        "Crafts & DIY",
        "Games & Puzzles",
        "Cars & Bikes",
        label="Topic",
    ),
    _section(
        "Reference & Professional",
        "reference",
        "Dictionaries",
        "Encyclopedias",
        "Almanacs & Yearbooks",
        "Handbooks & Manuals",
        "Legal Reference",
        "Medical Reference",
        "Technical Manuals",
        "Career Guides",
        label="Type",
    ),
    _section(
        "Journals, Magazines & Periodicals",
        "journals-magazines",
        "Academic & Research Journals",
        "News & Current Affairs Magazines",
        "Science & Technology Magazines",
        "Business Magazines",
        "Literary Magazines",
        "Lifestyle Magazines",
        "Comics Magazines",
        "Competitive Exam Magazines",
        label="Type",
    ),
    _section(
        "Notebooks, Diaries & Planners",
        "notebooks",
        "Blank Journals",
        "Notebooks",
        "Diaries",
        "Planners",
        label="Type",
    ),
    _section(
        "Rare & Collectible",
        "collectible",
        "Rare Books",
        "Antique Books",
        "First Editions",
        "Signed Copies",
        "Out of Print",
        "Box Sets & Special Editions",
        label="Type",
    ),
)

# Slugs from older seeds that the tree above replaces; they're switched off, not deleted.
RETIRED_SLUGS = ("textbooks", "computer-science")


def flatten(nodes: tuple[Node, ...] = TAXONOMY) -> list[FlatCategory]:
    out: list[FlatCategory] = []

    def walk(node: Node, parent: str | None, order: int, depth: int) -> None:
        slug = f"{parent}.{node.slug_part}" if parent else node.slug_part
        out.append(FlatCategory(slug, node.name, parent, node.child_label, order, depth))
        for i, child in enumerate(node.children):
            walk(child, slug, i, depth + 1)

    for i, root in enumerate(nodes):
        walk(root, None, i, 0)
    return out
