from rest_framework import serializers

from apps.accreditation.infrastructure.models import (
    Notary, AccreditationFile, PropertyDocument, DocumentType, REQUIRED_DOCUMENTS,
)
from apps.accreditation.domain.services import missing_documents


class NotarySerializer(serializers.ModelSerializer):
    files_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Notary
        fields = ['id', 'user', 'full_name', 'office', 'city', 'phone_number', 'email', 'is_active', 'files_count']


class NotaryPublicSerializer(serializers.ModelSerializer):
    """Version publique (page d'accueil) : sans coordonnées."""
    files_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Notary
        fields = ['id', 'full_name', 'office', 'city', 'files_count']


class PropertyDocumentSerializer(serializers.ModelSerializer):
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyDocument
        fields = ['id', 'doc_type', 'doc_type_display', 'status', 'status_display', 'comment', 'file_url', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if request and obj.file else None


class DocumentUploadSerializer(serializers.Serializer):
    doc_type = serializers.ChoiceField(choices=DocumentType.choices)
    file = serializers.FileField()


class AccreditationFileSerializer(serializers.ModelSerializer):
    property = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    notary = NotaryPublicSerializer(read_only=True)
    step_label = serializers.CharField(source='get_step_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents = PropertyDocumentSerializer(source='property.documents', many=True, read_only=True)
    checklist = serializers.SerializerMethodField()
    missing_documents = serializers.SerializerMethodField()

    class Meta:
        model = AccreditationFile
        fields = [
            'id', 'property', 'owner_name', 'notary', 'step', 'step_label', 'status', 'status_display',
            'certification_level', 'refusal_reason', 'submitted_at', 'updated_at', 'certified_at',
            'documents', 'checklist', 'missing_documents',
        ]

    def get_property(self, obj):
        p = obj.property
        cover = next((img for img in p.images.all() if img.is_cover), None) or next(iter(p.images.all()), None)
        return {
            'id': str(p.id), 'reference': p.reference, 'slug': p.slug, 'title': p.title,
            'commune': p.commune, 'neighborhood': p.neighborhood, 'status': p.status,
            'cover_image': cover.url(self.context.get('request')) if cover else None,
        }

    def get_owner_name(self, obj):
        owner = obj.property.owner
        return f"{owner.first_name} {owner.last_name}".strip() if owner else 'Thiebbro (mandat)'

    def get_checklist(self, obj):
        present = {d.doc_type for d in obj.property.documents.all() if d.status != 'REJETE'}
        return {d.value: d.value in present for d in DocumentType}

    def get_missing_documents(self, obj):
        return missing_documents(obj)


class AccreditationActionSerializer(serializers.Serializer):
    ACTIONS = ('assign', 'advance', 'certify', 'refuse')
    action = serializers.ChoiceField(choices=[(a, a) for a in ACTIONS])
    notary_id = serializers.UUIDField(required=False)
    level = serializers.CharField(required=False, default='VERIFIE')
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class DocumentReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyDocument
        fields = ['status', 'comment']


__all__ = [
    'NotarySerializer', 'NotaryPublicSerializer', 'PropertyDocumentSerializer', 'DocumentUploadSerializer',
    'AccreditationFileSerializer', 'AccreditationActionSerializer', 'DocumentReviewSerializer', 'REQUIRED_DOCUMENTS',
]
