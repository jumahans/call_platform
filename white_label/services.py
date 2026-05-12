from django.utils import timezone
from .models import WhiteLabel, WhiteLabelDomain
from accounts.models import User


class WhiteLabelService:

    @staticmethod
    def get_or_create(user: User) -> WhiteLabel:
        if not user.organization:
            raise ValueError("User has no organization")

        white_label, created = WhiteLabel.objects.get_or_create(
            organization=user.organization,
            defaults={
                'created_by': user,
                'company_name': user.organization.name,
                'status': WhiteLabel.Status.ACTIVE,
                'features': {
                    'rtb': True,
                    'ivr': True,
                    'dni': True,
                    'analytics': True,
                    'billing': True,
                    'white_label': True,
                    'api_access': True,
                }
            }
        )
        return white_label

    @staticmethod
    def get(user: User) -> WhiteLabel:
        try:
            return WhiteLabel.objects.prefetch_related('domains').get(
                organization=user.organization
            )
        except WhiteLabel.DoesNotExist:
            return WhiteLabelService.get_or_create(user)

    @staticmethod
    def update(data, user: User) -> WhiteLabel:
        white_label = WhiteLabelService.get(user)

        fields = [
            'company_name', 'logo_url', 'favicon_url',
            'support_email', 'support_phone', 'website_url',
            'primary_color', 'secondary_color', 'accent_color',
            'background_color', 'text_color', 'custom_css',
            'email_header', 'email_footer', 'email_from_name',
            'email_from_address', 'features'
        ]

        for field in fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(white_label, field, value)

        white_label.save()
        return white_label

    @staticmethod
    def add_domain(data, user: User) -> WhiteLabelDomain:
        white_label = WhiteLabelService.get(user)

        if WhiteLabelDomain.objects.filter(domain=data.domain).exists():
            raise ValueError("Domain already exists")

        if data.is_primary:
            WhiteLabelDomain.objects.filter(
                white_label=white_label,
                is_primary=True
            ).update(is_primary=False)

        domain = WhiteLabelDomain.objects.create(
            white_label=white_label,
            domain=data.domain,
            is_primary=data.is_primary,
            status=WhiteLabelDomain.Status.PENDING
        )

        return domain

    @staticmethod
    def verify_domain(domain_id: str, user: User) -> WhiteLabelDomain:
        white_label = WhiteLabelService.get(user)

        try:
            domain = WhiteLabelDomain.objects.get(
                id=domain_id,
                white_label=white_label
            )
        except WhiteLabelDomain.DoesNotExist:
            raise ValueError("Domain not found")

        domain.status = WhiteLabelDomain.Status.ACTIVE
        domain.verified_at = timezone.now()
        domain.save()

        return domain

    @staticmethod
    def remove_domain(domain_id: str, user: User):
        white_label = WhiteLabelService.get(user)

        try:
            domain = WhiteLabelDomain.objects.get(
                id=domain_id,
                white_label=white_label
            )
            domain.delete()
        except WhiteLabelDomain.DoesNotExist:
            raise ValueError("Domain not found")

    @staticmethod
    def get_by_domain(domain: str) -> WhiteLabel:
        try:
            wl_domain = WhiteLabelDomain.objects.select_related(
                'white_label__organization'
            ).get(domain=domain, status=WhiteLabelDomain.Status.ACTIVE)
            return wl_domain.white_label
        except WhiteLabelDomain.DoesNotExist:
            return None

    @staticmethod
    def format(white_label: WhiteLabel) -> dict:
        domains = [
            {
                'id': str(d.id),
                'domain': d.domain,
                'is_primary': d.is_primary,
                'status': d.status,
                'verified_at': d.verified_at.isoformat() if d.verified_at else None,
                'created_at': d.created_at.isoformat(),
            }
            for d in white_label.domains.all()
        ]

        return {
            'id': str(white_label.id),
            'company_name': white_label.company_name,
            'logo_url': white_label.logo_url,
            'favicon_url': white_label.favicon_url,
            'support_email': white_label.support_email,
            'support_phone': white_label.support_phone,
            'website_url': white_label.website_url,
            'primary_color': white_label.primary_color,
            'secondary_color': white_label.secondary_color,
            'accent_color': white_label.accent_color,
            'background_color': white_label.background_color,
            'text_color': white_label.text_color,
            'custom_css': white_label.custom_css,
            'email_header': white_label.email_header,
            'email_footer': white_label.email_footer,
            'email_from_name': white_label.email_from_name,
            'email_from_address': white_label.email_from_address,
            'features': white_label.features,
            'status': white_label.status,
            'organization_id': str(white_label.organization_id),
            'domains': domains,
            'created_at': white_label.created_at.isoformat(),
            'updated_at': white_label.updated_at.isoformat(),
        }