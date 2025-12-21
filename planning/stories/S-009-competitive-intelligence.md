# S-009: Competitive Intelligence

**Story Type:** User Story
**Priority:** Low
**Epoch:** 5 (alongside CRM)
**Status:** PENDING
**Module:** django-competitive-intel

## User Story

**As a** clinic owner
**I want to** monitor my competitors' activities, pricing, and market presence
**So that** I can make informed business decisions and maintain competitive advantage

**As a** clinic owner
**I want to** know when competitors visit my website
**So that** I can understand their interest in my business and adjust strategy accordingly

## Acceptance Criteria

### Competitor Profiles
- [ ] Create and manage competitor profiles
- [ ] Store competitor details (name, address, phone, hours, services)
- [ ] GPS coordinates for map visualization
- [ ] Link to social media profiles
- [ ] Notes and observations field
- [ ] Last updated timestamp

### Competitor Map
- [ ] Interactive map showing all competitors
- [ ] Pet-Friendly location highlighted differently
- [ ] Click marker to see competitor details
- [ ] Distance calculation from Pet-Friendly
- [ ] Service area visualization (optional)

### Price Tracking
- [ ] Track competitor pricing for services
- [ ] Historical price data with timestamps
- [ ] Price comparison charts
- [ ] Alert when competitor changes prices
- [ ] Export price comparison reports

### Advertising Tracker
- [ ] Monitor competitor Facebook/Instagram ads
- [ ] Track Google Ads presence
- [ ] Log advertising campaigns observed
- [ ] Screenshot/evidence storage
- [ ] Spending estimates (if available)

### Website Visitor Intelligence
- [ ] Track IP addresses visiting Pet-Friendly website
- [ ] Identify known competitor IPs
- [ ] Log visit patterns (pages, duration, frequency)
- [ ] Alert when competitor visits
- [ ] Geographic analysis of visitors
- [ ] Privacy-compliant implementation

### Dashboard & Reports
- [ ] Competitive intelligence dashboard
- [ ] AI-generated insights and recommendations
- [ ] Weekly/monthly summary reports
- [ ] Trend analysis
- [ ] Actionable recommendations

## Technical Requirements

### Models

```python
# Competitor Profiles
class Competitor(models.Model):
    """Competitor business profile"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Social media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    # Business details
    hours = models.JSONField(default=dict)  # {mon: "9-5", tue: "9-5", ...}
    services = models.JSONField(default=list)  # ["consultations", "surgery", ...]

    # Metadata
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Known IP addresses for visitor tracking
    known_ips = models.JSONField(default=list)

    class Meta:
        ordering = ['name']


class CompetitorPricing(models.Model):
    """Track competitor service pricing over time"""
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='MXN')
    source = models.CharField(max_length=100)  # "phone call", "website", "visit"
    observed_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-observed_at']


class CompetitorAd(models.Model):
    """Track competitor advertising campaigns"""
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)  # facebook, instagram, google
    ad_type = models.CharField(max_length=50)  # image, video, carousel, search
    content = models.TextField(blank=True)  # Ad copy/description
    screenshot = models.ImageField(upload_to='competitor_ads/', null=True)
    landing_url = models.URLField(blank=True)
    estimated_spend = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-first_seen']


# Website Visitor Intelligence
class WebsiteVisitor(models.Model):
    """Track website visitors with IP intelligence"""
    ip_address = models.GenericIPAddressField()

    # Geolocation (from IP lookup)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    isp = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)

    # Classification
    is_competitor = models.BooleanField(default=False)
    competitor = models.ForeignKey(
        Competitor, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_bot = models.BooleanField(default=False)

    # Aggregated stats
    first_visit = models.DateTimeField()
    last_visit = models.DateTimeField()
    total_visits = models.IntegerField(default=1)
    total_pageviews = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_visit']


class PageView(models.Model):
    """Individual page view tracking"""
    visitor = models.ForeignKey(WebsiteVisitor, on_delete=models.CASCADE)
    path = models.CharField(max_length=500)
    referrer = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)

    # Session data
    session_id = models.CharField(max_length=100, blank=True)
    duration_seconds = models.IntegerField(null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


class CompetitorAlert(models.Model):
    """Alerts for competitive intelligence events"""
    ALERT_TYPES = [
        ('competitor_visit', 'Competitor Website Visit'),
        ('price_change', 'Price Change Detected'),
        ('new_ad', 'New Advertisement'),
        ('social_activity', 'Social Media Activity'),
    ]

    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    competitor = models.ForeignKey(
        Competitor, on_delete=models.CASCADE, null=True, blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, default='info')  # info, warning, important

    # Related objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True)
    read_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class CompetitiveInsight(models.Model):
    """AI-generated competitive insights"""
    insight_type = models.CharField(max_length=50)  # pricing, advertising, traffic, opportunity
    title = models.CharField(max_length=200)
    summary = models.TextField()
    detailed_analysis = models.TextField()
    recommendations = models.JSONField(default=list)  # List of action items

    # Supporting data
    data_sources = models.JSONField(default=list)  # What data was analyzed
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0

    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True)
    is_actionable = models.BooleanField(default=True)

    # Tracking
    is_dismissed = models.BooleanField(default=False)
    dismissed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dismissed_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

### AI Tools

```python
COMPETITIVE_INTEL_TOOLS = [
    {
        "name": "get_competitor_map",
        "description": "Get competitor locations for map display",
        "parameters": {
            "type": "object",
            "properties": {
                "include_inactive": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "get_competitor_details",
        "description": "Get detailed information about a competitor",
        "parameters": {
            "type": "object",
            "properties": {
                "competitor_id": {"type": "integer"}
            },
            "required": ["competitor_id"]
        }
    },
    {
        "name": "compare_pricing",
        "description": "Compare pricing between Pet-Friendly and competitors",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"},
                "competitor_ids": {"type": "array", "items": {"type": "integer"}}
            }
        }
    },
    {
        "name": "get_competitor_visits",
        "description": "Get recent website visits from competitor IPs",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 30},
                "competitor_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_competitive_insights",
        "description": "Get AI-generated competitive insights",
        "parameters": {
            "type": "object",
            "properties": {
                "insight_type": {
                    "type": "string",
                    "enum": ["pricing", "advertising", "traffic", "opportunity", "all"]
                },
                "limit": {"type": "integer", "default": 5}
            }
        }
    },
    {
        "name": "log_competitor_pricing",
        "description": "Log a competitor's pricing information",
        "parameters": {
            "type": "object",
            "properties": {
                "competitor_id": {"type": "integer"},
                "service_name": {"type": "string"},
                "price": {"type": "number"},
                "source": {"type": "string"}
            },
            "required": ["competitor_id", "service_name", "price", "source"]
        }
    },
    {
        "name": "log_competitor_ad",
        "description": "Log a competitor's advertisement",
        "parameters": {
            "type": "object",
            "properties": {
                "competitor_id": {"type": "integer"},
                "platform": {"type": "string", "enum": ["facebook", "instagram", "google"]},
                "ad_type": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["competitor_id", "platform"]
        }
    },
    {
        "name": "generate_competitive_report",
        "description": "Generate a competitive analysis report",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["weekly_summary", "pricing_analysis", "market_position", "full_report"]
                },
                "format": {"type": "string", "enum": ["pdf", "html", "json"]}
            },
            "required": ["report_type"]
        }
    }
]
```

## Example AI Conversations

### Competitor Visit Alert
```
AI: Alert: Competitor website visit detected

    A visitor from Fauna Silvestre's known IP address
    visited your website today.

    Visit Details:
    - Time: 2:34 PM
    - Pages Viewed: Services, Pricing, About Us
    - Duration: 4 minutes 23 seconds
    - This is their 3rd visit this month

    This could indicate they're monitoring your services
    and pricing. Consider this when planning promotions.

Dr. Pablo: What pages do they look at most?

AI: Based on Fauna Silvestre's 8 visits over the past 3 months:

    Most Viewed Pages:
    1. Services Page (8 visits, 100%)
    2. Pricing/Rates (6 visits, 75%)
    3. About Us (4 visits, 50%)
    4. Store Products (2 visits, 25%)

    Pattern: They consistently check your services and
    pricing, suggesting they're benchmarking against you.

    Recommendation: They may be adjusting their offerings
    to compete. Consider highlighting your unique services
    (AI booking, 24hr support) that they can't easily copy.
```

### Price Comparison
```
Dr. Pablo: How do my prices compare to competitors?

AI: Here's your pricing comparison for common services:

    Service          | Pet-Friendly | Fauna S. | Miramar
    -----------------+--------------+----------+---------
    Consultation     | $350 MXN     | $400 MXN | $300 MXN
    Vaccination      | $250 MXN     | $280 MXN | $220 MXN
    Dental Cleaning  | $1,200 MXN   | $1,500 MXN | N/A
    Spay (cat)       | $800 MXN     | $900 MXN | $750 MXN

    Analysis:
    - You're competitively priced in the middle
    - Fauna Silvestre is premium-priced
    - Miramar is budget-positioned

    Your AI booking and modern website justify premium
    positioning. Consider emphasizing convenience value.
```

## Privacy & Compliance

### IP Tracking Compliance
- Display clear privacy policy on website
- IP addresses stored for legitimate business interest
- No personal identification without consent
- Data retention policy (90 days default)
- GDPR-compliant data handling
- Option to exclude from tracking (cookie consent)

### Ethical Guidelines
- Only track publicly available information
- No unauthorized access to competitor systems
- No employee poaching intelligence
- Transparent about competitive monitoring
- Focus on improving own services, not sabotage

## Package Structure

```
django-competitive-intel/
├── competitive_intel/
│   ├── __init__.py
│   ├── models.py           # Competitor, Pricing, Ads, Visitors
│   ├── admin.py            # Admin interface
│   ├── views.py            # Dashboard, map, reports
│   ├── api/
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   └── views.py        # REST API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ip_lookup.py    # IP geolocation
│   │   ├── visitor_tracking.py
│   │   ├── insights.py     # AI insight generation
│   │   └── reports.py      # Report generation
│   ├── middleware.py       # Visitor tracking middleware
│   ├── signals.py          # Alert generation
│   ├── templates/
│   │   └── competitive_intel/
│   │       ├── dashboard.html
│   │       ├── map.html
│   │       ├── competitor_detail.html
│   │       └── reports/
│   ├── static/
│   │   └── competitive_intel/
│   │       ├── js/
│   │       │   └── map.js
│   │       └── css/
│   └── management/
│       └── commands/
│           ├── import_competitors.py
│           └── generate_insights.py
├── tests/
├── setup.py
├── pyproject.toml
└── README.md
```

## Definition of Done

- [ ] Competitor model with CRUD operations
- [ ] Interactive competitor map (Leaflet.js)
- [ ] Price tracking with history
- [ ] Advertising tracker with screenshots
- [ ] IP visitor tracking middleware
- [ ] Competitor IP identification
- [ ] Alert system for competitor visits
- [ ] AI insight generation
- [ ] Dashboard with all metrics
- [ ] Privacy-compliant implementation
- [ ] Export reports (PDF, CSV)
- [ ] Tests written and passing (>95% coverage)
- [ ] Package pip-installable

## Dependencies

- S-001: Foundation (models, auth)
- S-002: AI Chat (for insights queries)
- S-007: CRM (shares visitor tracking patterns)

## Reusability

This package is designed to work for any business:
- Replace "Competitor" with industry-appropriate terminology
- Configurable tracking parameters
- Pluggable IP lookup services
- Customizable alert rules
- Industry-agnostic insights engine

## Notes

- Consider IP2Location or MaxMind for geolocation
- Rate limit IP lookups to manage API costs
- Batch process insights generation (daily cron)
- Consider competitor social media API monitoring (future)
- Mobile app competitor analysis (future enhancement)
