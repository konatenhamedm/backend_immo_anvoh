"""Photos optimisées à l'envoi, programmes : échéancier de paiement, plans et documents."""

import shutil
import tempfile
from decimal import Decimal
from io import BytesIO
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.properties.infrastructure.models import DevelopmentProject, Property, PropertyImage, PropertyStatus
from apps.users.infrastructure.models import User, UserRole

MEDIA = tempfile.mkdtemp(prefix="thiebbro-test-media-")


def png(width, height, mode="RGB", color=(30, 90, 200)):
    buf = BytesIO()
    Image.new(mode, (width, height), color).save(buf, format="PNG")
    return SimpleUploadedFile("photo.png", buf.getvalue(), content_type="image/png")


def make_user(email, role):
    return User.objects.create_user(email=email, password="Un-Mot2Passe-Solide", first_name="T", last_name="N", phone_number="+2250700000000", role=role)


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def open_stored(field_file):
    field_file.open("rb")
    try:
        img = Image.open(BytesIO(field_file.read()))
        img.load()
        return img
    finally:
        field_file.close()


@override_settings(MEDIA_ROOT=MEDIA)
class PhotoOptimizationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.owner = make_user("owner@test.ci", UserRole.PROPRIETAIRE)
        self.prop = Property.objects.create(title="Villa", description="d", property_type="VILLA", price=Decimal("1"), commune="Cocody", neighborhood="Angré", surface_sqm=Decimal("90"), status=PropertyStatus.DISPONIBLE, owner=self.owner)

    def _upload(self, f):
        return client_for(self.owner).post(f"/api/v1/properties/{self.prop.id}/images/", {"image": f}, format="multipart")

    def test_big_photo_is_resized_recompressed_and_gets_a_thumbnail(self):
        original = png(4000, 3000)
        original_size = original.size
        r = self._upload(original)
        self.assertEqual(r.status_code, 201)
        photo = PropertyImage.objects.get()
        full, thumb = open_stored(photo.image), open_stored(photo.thumbnail)
        self.assertEqual(full.format, "JPEG")
        self.assertEqual(full.size, (1600, 1200))  # grand côté ramené à 1600, proportions gardées
        self.assertEqual(thumb.size, (480, 360))
        self.assertLess(photo.image.size, original_size)
        self.assertLess(photo.thumbnail.size, photo.image.size)
        self.assertTrue(r.data["thumbnail_url"].endswith(".jpg"))

    def test_small_photo_is_never_enlarged(self):
        self._upload(png(300, 200))
        photo = PropertyImage.objects.get()
        self.assertEqual(open_stored(photo.image).size, (300, 200))
        self.assertEqual(open_stored(photo.thumbnail).size, (300, 200))

    def test_phone_photo_orientation_is_applied(self):
        buf = BytesIO()
        img = Image.new("RGB", (200, 100), (200, 30, 30))
        exif = Image.Exif()
        exif[0x0112] = 6  # « à pivoter de 90° » : photo prise à la verticale
        img.save(buf, format="JPEG", exif=exif)
        self._upload(SimpleUploadedFile("tel.jpg", buf.getvalue(), content_type="image/jpeg"))
        self.assertEqual(open_stored(PropertyImage.objects.get().image).size, (100, 200))

    def test_transparent_png_is_flattened_on_white(self):
        self._upload(png(50, 50, mode="RGBA", color=(0, 0, 0, 0)))
        px = open_stored(PropertyImage.objects.get().image).getpixel((25, 25))
        self.assertTrue(all(c >= 250 for c in px), px)

    def test_non_image_and_oversized_files_are_refused(self):
        r = self._upload(SimpleUploadedFile("virus.png", b"MZ\x90 pas une image", content_type="image/png"))
        self.assertEqual(r.status_code, 400)
        with mock.patch("apps.properties.interfaces.serializers.MAX_UPLOAD_BYTES", 100):
            r = self._upload(png(400, 400))
        self.assertEqual(r.status_code, 400)
        self.assertIn("trop lourde", str(r.data))
        self.assertEqual(PropertyImage.objects.count(), 0)

    def test_external_urls_are_untouched_and_card_exposes_the_thumbnail(self):
        PropertyImage.objects.create(property=self.prop, external_url="https://images.example/a.jpg", is_cover=True)
        card = APIClient().get(f"/api/v1/properties/{self.prop.id}/").data
        self.assertEqual(card["cover_image"], "https://images.example/a.jpg")
        self.assertIsNone(card["cover_thumb"])  # pas de miniature pour une image externe : le site retombe sur l'image
        self._upload(png(1000, 800))
        listing = APIClient().get("/api/v1/properties/search/").data["results"][0]
        self.assertIn("cover_thumb", listing)


@override_settings(MEDIA_ROOT=MEDIA)
class ProjectPaymentAndDocumentsTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin@test.ci", UserRole.ADMIN)
        self.buyer = make_user("buyer@test.ci", UserRole.PARTICULIER)
        self.project = DevelopmentProject.objects.create(name="Résidence Test", developer_name="SCI", commune="Cocody", neighborhood="Angré", description="d", starting_price=Decimal("30000000"))

    def _doc(self, name="plan.pdf", content=b"%PDF-1.4 test", **extra):
        return {"title": "Plan de masse", "kind": "PLAN", "file": SimpleUploadedFile(name, content, content_type="application/pdf"), **extra}

    def test_team_can_add_and_remove_plans_and_documents(self):
        c = client_for(self.admin)
        r = c.post(f"/api/v1/properties/projects/{self.project.id}/documents/", self._doc(), format="multipart")
        self.assertEqual(r.status_code, 201)
        self.assertEqual((r.data["kind_display"], r.data["format"]), ("Plan", "pdf"))
        public = APIClient().get(f"/api/v1/properties/projects/slug/{self.project.slug}/").data
        self.assertEqual([d["title"] for d in public["documents"]], ["Plan de masse"])
        self.assertTrue(public["documents"][0]["url"].startswith("http"))
        self.assertEqual(c.delete(f"/api/v1/properties/projects/documents/{r.data['id']}/").status_code, 204)
        self.assertEqual(APIClient().get(f"/api/v1/properties/projects/slug/{self.project.slug}/").data["documents"], [])

    def test_only_the_team_can_upload_and_only_safe_formats(self):
        url = f"/api/v1/properties/projects/{self.project.id}/documents/"
        self.assertEqual(client_for(self.buyer).post(url, self._doc(), format="multipart").status_code, 403)
        self.assertEqual(APIClient().post(url, self._doc(), format="multipart").status_code, 401)
        bad = client_for(self.admin).post(url, self._doc(name="installer.exe", content=b"MZ"), format="multipart")
        self.assertEqual(bad.status_code, 400)
        with mock.patch.object(__import__("apps.properties.interfaces.serializers", fromlist=["x"]).ProjectDocumentUploadSerializer, "MAX_BYTES", 5):
            big = client_for(self.admin).post(url, self._doc(content=b"%PDF-1.4 plus de cinq octets"), format="multipart")
        self.assertEqual(big.status_code, 400)
        self.assertEqual(self.project.documents.count(), 0)

    def test_payment_schedule_is_saved_and_cannot_exceed_100_percent(self):
        c = client_for(self.admin)
        url = f"/api/v1/properties/projects/{self.project.id}/"
        ok = c.patch(url, {"payment_schedule": [{"label": "Réservation", "percent": 10}, {"label": "Fondations", "percent": 30}, {"label": "Livraison", "percent": 60}], "payment_notes": "Paiement par virement."}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual([s["percent"] for s in APIClient().get(f"/api/v1/properties/projects/slug/{self.project.slug}/").data["payment_schedule"]], [10, 30, 60])
        too_much = c.patch(url, {"payment_schedule": [{"label": "A", "percent": 70}, {"label": "B", "percent": 40}]}, format="json")
        self.assertEqual(too_much.status_code, 400)
        self.assertEqual(c.patch(url, {"payment_schedule": [{"label": "A", "percent": -5}]}, format="json").status_code, 400)
