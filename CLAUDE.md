# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is PRPC (푸른마취통증의학과의원) - a Django-based hospital reservation system that manages online appointments and prevents conflicts between online bookings and phone consultations. The system has been in operation since 2010.

## Architecture

### Django Project Structure
- **Main project**: `hospital_test/` (Django project root)
- **Settings**: Split settings in `hospital_test/settings/` (base.py, local.py, deploy.py)  
- **Apps**: 9 Django apps, each handling specific functionality
- **Database**: SQLite for local/development, supports PostgreSQL for production
- **Caching**: Local memory cache for booking blocks, Redis recommended for production

### Core Applications
- `accountapp` - User authentication and account management
- `profileapp` - Patient profiles with chart numbers and medical info
- `bookingapp` - Online appointment booking system
- `superapp` - Admin tools for hospital staff (superusers only)
- `articleapp` - Content management and homepage
- `noteapp` - Internal messaging between staff and patients
- `passwordapp` - Password reset functionality  
- `searchapp` - Patient search for staff
- `logapp` - Booking change audit trail and log management system

### Key Features
- **Booking Conflicts Prevention**: Cache-based temporary blocking system (3-minute auto-release)
- **Multi-role Access**: Regular users (patients) vs superusers (hospital staff)
- **Real-time Updates**: Discord webhooks, SMS, and Line notifications
- **Korean Localization**: Korean language, Asia/Seoul timezone, Korean fonts
- **Audit Trail**: BookingLog model tracks all reservation changes with IP addresses and timestamps
- **UI/UX Consistency**: Unified card-based design system with pastel color palette
- **Responsive Design**: Mobile-optimized responsive design with Bootstrap 5

## Common Commands

### Development
```bash
# Run development server
python manage.py runserver

# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Django shell
python manage.py shell
```

### Database Operations
```bash
# Reset database (SQLite)
rm db.sqlite3
python manage.py migrate

# Load fixtures (if any)
python manage.py loaddata fixtures/initial_data.json
```

### Docker Operations  
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in production mode
docker-compose -f docker-compose.yml up -d
```

## Development Guidelines

### Settings Management
- Use `hospital_test.settings.local` for development (default in manage.py)
- Environment variables loaded from `.env` file in project root
- Critical config: `SECRET_KEY`, `EMAIL_HOST_PASSWORD`, Discord webhook URLs

### Database Models Key Relationships
- `User` (Django built-in) ↔ `Profile` (OneToOne)
- `User` → `Booking` (ForeignKey) 
- `User` → `Note` (sender/recipient ForeignKeys)
- `User` → `BookingLog` (ForeignKey, as user and modified_by)
- `Booking` → `BookingLog` (OneToMany relationship)
- Cache-based booking blocks (not persisted to DB)

### URL Structure
- Root (`/`) - Homepage with waiting patient count
- `/accounts/` - Authentication flows
- `/profiles/` - Patient profile management  
- `/bookings/` - Online reservation system
- `/supers/` - Staff admin tools (superuser required)
- `/articles/` - Static content pages
- `/notes/` - Internal messaging
- `/searches/` - Patient search
- `/logs/` - Booking change logs (superuser required)

### Template Architecture
- Base template: `templates/base.html` with Bootstrap 5
- Shared components: `head.html`, `header.html`, `footer.html`
- App-specific templates in each app's `templates/` directory
- Korean fonts: NanumSquare series in `static/fonts/`
- **Design System**: Unified card-based components (info-card, content-item patterns)
- **Color Palette**: Consistent pastel colors (#3b82f6, #10b981, #f59e0b, #ef4444, etc.)

### Authentication & Permissions
- Standard Django authentication with custom login/logout flows
- Profile creation required after account signup (CheckProfileMiddleware)
- Superuser decorators for staff-only functionality
- Login redirect: articles index, Logout redirect: login page

### Cache Implementation
- **Local Memory Cache**: Default for development (5-minute timeout)
- **Booking Blocks**: 3-minute temporary reservation conflicts prevention  
- **Redis**: Recommended for production (`BOOKING_BLOCK_TIMEOUT`, `BOOKING_BLOCK_PERIOD_DAYS`)

### Notification Systems
- **Email**: SMTP via Naver (prpc8575@naver.com)
- **Discord**: Dual webhook system with encrypted URLs
- **Integration**: Triggered on booking status changes

### Time Management
- **Timezone**: Asia/Seoul (USE_TZ = False)
- **Booking Times**: 09:20 to 20:05 in 25-minute intervals
- **Date Format**: YYYY-MM-DD, Time Format: HH:MM

## UI/UX Design System

### Card-Based Components
```css
.info-card {
    background: white;
    border-radius: 20px;
    padding: 2.5rem;
    box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1);
    border: 1px solid #f1f5f9;
    position: relative;
    overflow: hidden;
}

.content-item {
    background: [pastel-color];
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid [border-color];
    margin-bottom: 1rem;
}
```

### Pastel Color System
- **Blue**: `#3b82f6` (Primary actions, info)
- **Green**: `#10b981` (Success, approval)
- **Orange**: `#f59e0b` (Warning, pending)
- **Red**: `#ef4444` (Error, deletion)
- **Purple**: `#8b5cf6` (Special features)
- **Cyan**: `#06b6d4` (Communication)

### Responsive Design Patterns
- Mobile-first approach with Bootstrap 5
- Breakpoints: 576px (sm), 768px (md), 992px (lg)
- Consistent padding and margin scaling
- Touch-friendly button sizes (min 44px)

## Logging System

### BookingLog Model Structure
```python
class BookingLog(models.Model):
    ACTION_TYPES = (
        ('CREATE', '예약 생성'),
        ('UPDATE', '예약 변경'),
        ('DELETE', '예약 취소'),
        ('APPROVE', '예약 승인'),
        ('REJECT', '예약 거절'),
        ('BLOCK', '예약 차단'),
        ('UNBLOCK', '예약 차단 해제'),
    )
    
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    user = models.ForeignKey(User, related_name='booking_logs_as_user')
    modified_by = models.ForeignKey(User, related_name='booking_logs_as_modifier')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # ... additional fields
```

### Log Tracking Features
- **Complete Audit Trail**: Every booking action is logged
- **User Context**: Both booking user and modifier are tracked
- **IP Tracking**: Source IP addresses for security
- **Temporal Data**: Preserves booking info even after deletion
- **Status Changes**: Previous and new status tracking

## Testing and Quality

### Manual Testing Focus Areas
- Booking conflict prevention (cache-based blocking)
- Superuser permission boundaries  
- Profile completion middleware
- Multi-timezone booking calculations
- Discord notification delivery

### Security Considerations
- Environment variables for secrets (never commit .env)
- Superuser-only access to admin functions
- CSRF protection on all forms
- User isolation (patients can only see own data)

## Deployment Notes

### Environment Variables Required
```
SECRET_KEY=
EMAIL_HOST_PASSWORD=
DISCORD_WEBHOOK_URL_1=
DISCORD_WEBHOOK_URL_2=
```

### AWS Server Deployment
- **Container Platform**: Docker with Portainer management
- **Process**: GitHub → Dockerfile → Portainer → Docker Compose Stack
- **Migration Strategy**: Include `makemigrations` and `migrate` in Dockerfile CMD
- **Deployment Guide**: Refer to `deploy.txt` for step-by-step process

### Static Files
- Development: Served by Django (`/static/`)
- Production: Collect to `staticfiles/` directory
- Media files: Stored in `../../media/` (relative to project root)

### Docker Configuration
```dockerfile
# Key deployment commands in Dockerfile
CMD ["bash", "-c", "python manage.py collectstatic --noinput --settings=hospital_test.settings.deploy && python manage.py makemigrations --settings=hospital_test.settings.deploy && python manage.py migrate --settings=hospital_test.settings.deploy && gunicorn hospital_test.wsgi --env DJANGO_SETTINGS_MODULE=hospital_test.settings.deploy --bind 0.0.0.0:8000"]
```
- Nginx configuration for reverse proxy
- Gunicorn WSGI server for production
- **Migration Inclusion**: Automatic DB schema updates on deployment

## Troubleshooting

### Common Issues
- **Profile Missing Error**: User must complete profile after signup
- **Booking Conflicts**: Check cache backend configuration  
- **Permission Denied**: Verify superuser status for admin functions
- **Time Zone Issues**: Ensure USE_TZ = False and TIME_ZONE = 'Asia/Seoul'

### Debug Settings
- `DEBUG = True` in local.py for development
- Check `ALLOWED_HOSTS = ["*"]` for local development
- Database path: `BASE_DIR / 'db.sqlite3'`

## Development Tools

### MCP (Model Context Protocol)
- **Git Server**: `mcp-server-git` for local Git operations
- **Fetch Server**: `mcp-server-fetch` for HTTP API requests
- **GitHub Integration**: PyGithub for GitHub API operations

### Code Development
- **IDE Integration**: Optimized for Claude Code
- **Git Workflow**: Feature branch → PR → Main branch merge
- **Branch Naming**: `feature/description` or `fix/issue-description`

### Documentation
- **Project Guide**: This CLAUDE.md file
- **Deployment Guide**: `deploy.txt` for AWS server deployment
- **API Documentation**: Available in Django admin interface

---
## Document Information

**Last Updated**: 2025년 9월 6일  
**Major Contributors**: Claude Code, Development Team  
**Version**: 2.0 (UI/UX Redesign + Logging System)  
**Related Files**: `deploy.txt`, `requirements.txt`, `Dockerfile`