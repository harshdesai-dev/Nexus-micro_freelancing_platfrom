from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from authentication.views import body, error, role_required, success
from .models import Verification, VerificationHistory


@csrf_exempt
@require_http_methods(["POST"])
@role_required("STUDENT")
def verification_view(request):
    data = body(request)
    if data is None:
        return error("INVALID_JSON", "Invalid JSON in request body.")
    file_reference = str(data.get("college_id_file_reference", "")).strip()
    if not file_reference:
        return error("VALIDATION_ERROR", "college_id_file_reference is required.")
    try:
        verification = Verification.objects.create(
            student=request.user,
            college_id_file=file_reference,
            college_name=str(data.get("college_name", "")),
            course=str(data.get("course", "")),
            academic_year=str(data.get("academic_year", "")),
        )
    except IntegrityError:
        return error("VERIFICATION_PENDING", "A pending verification already exists for this student.", 409)
    VerificationHistory.objects.create(
        verification=verification,
        previous_status="",
        new_status=Verification.Status.PENDING,
        action="Verification submitted",
        actor=request.user,
    )
    return success({"id": str(verification.id), "status": verification.status}, "Verification submitted", 201)
