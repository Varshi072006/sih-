from __future__ import annotations

import hashlib
import hmac
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AadhaarVerification, IdentityVerificationConsent, User
from app.services.audit import AuditLogService
from app.utils.verhoeff import mask_aadhaar, validate_aadhaar_number


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_aadhaar_token(aadhaar_number: str) -> str:
    """
    Computes a privacy-preserving cryptographic token (HMAC-SHA256) of the Aadhaar number.
    This token is used for unique identity matching / duplicate detection
    without ever storing or exposing the plaintext 12-digit Aadhaar number.
    """
    cleaned = aadhaar_number.replace(" ", "").replace("-", "").strip()
    return hmac.new(
        settings.AADHAAR_TOKEN_SALT.encode("utf-8"),
        cleaned.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class AadhaarVerificationProvider(ABC):
    """
    Abstract interface for Aadhaar OTP authentication / e-KYC.
    Decouples the core registration logic from any specific vendor/provider.
    """

    provider_name: str = "base_provider"
    is_demo: bool = False

    @abstractmethod
    async def request_otp(
        self,
        aadhaar_number: str,
        consent_reference: str,
        client_ip: str = "",
    ) -> dict[str, Any]:
        """
        Request OTP generation from the authorized Aadhaar provider.
        Returns provider reference, masked mobile, and validity info.
        """
        pass

    @abstractmethod
    async def verify_otp(
        self,
        provider_reference: str,
        otp: str,
    ) -> dict[str, Any]:
        """
        Validates the OTP with the authorized Aadhaar provider.
        """
        pass

    @abstractmethod
    async def resend_otp(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        """
        Requests OTP resend from the provider.
        """
        pass

    @abstractmethod
    async def cancel(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        """
        Cancels an in-progress verification session.
        """
        pass

    @abstractmethod
    async def get_status(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        """
        Fetches current verification session status from the provider.
        """
        pass


class MockAadhaarVerificationProvider(AadhaarVerificationProvider):
    """
    Development/Demo implementation of Aadhaar Verification.
    Clearly labelled as Mock/Demo to prevent confusion with real UIDAI authentication.
    Used exclusively in development, testing, and evaluation environments.
    """

    provider_name = "MockAadhaarVerificationProvider (DEMO)"
    is_demo = True

    async def request_otp(
        self,
        aadhaar_number: str,
        consent_reference: str,
        client_ip: str = "",
    ) -> dict[str, Any]:
        cleaned = aadhaar_number.replace(" ", "").replace("-", "").strip()
        last4 = cleaned[-4:] if len(cleaned) >= 4 else "0000"
        # Deterministic demo registered mobile: ****** + last 4 digits
        masked_mobile = f"******{last4}"
        ref = f"DEMO-TXN-{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "status": "OTP_SENT",
            "provider": self.provider_name,
            "provider_reference": ref,
            "masked_mobile": masked_mobile,
            "expires_in_seconds": settings.AADHAAR_OTP_EXPIRY_SECONDS,
            "is_demo": True,
            "demo_notice": "DEMO MODE ONLY: No real Aadhaar request is being made. Use demo OTP to verify.",
        }

    async def verify_otp(
        self,
        provider_reference: str,
        otp: str,
    ) -> dict[str, Any]:
        # Handle specialized testing inputs
        if otp == "000000":
            return {
                "success": False,
                "status": "FAILED",
                "error_code": "INCORRECT_OTP",
                "error_message": "The OTP entered is incorrect. Please try again.",
            }
        if otp == "999999":
            return {
                "success": False,
                "status": "EXPIRED",
                "error_code": "EXPIRED_OTP",
                "error_message": "This OTP has expired. Please request a new OTP.",
            }
        if otp == "888888":
            return {
                "success": False,
                "status": "PROVIDER_ERROR",
                "error_code": "PROVIDER_ERROR",
                "error_message": "Aadhaar verification is temporarily unavailable. Please try again later.",
            }

        # Check configured demo OTP (default '123456')
        expected_otp = settings.DEMO_AADHAAR_OTP or "123456"
        if otp.strip() == expected_otp.strip():
            return {
                "success": True,
                "status": "VERIFIED",
                "provider": self.provider_name,
                "provider_reference": provider_reference,
                "verified_at": _utcnow(),
                "is_demo": True,
            }
        else:
            return {
                "success": False,
                "status": "FAILED",
                "error_code": "INCORRECT_OTP",
                "error_message": "The OTP entered is incorrect. Please try again.",
            }

    async def resend_otp(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "status": "OTP_SENT",
            "provider": self.provider_name,
            "provider_reference": provider_reference,
            "expires_in_seconds": settings.AADHAAR_OTP_EXPIRY_SECONDS,
            "is_demo": True,
        }

    async def cancel(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "status": "CANCELLED",
            "provider_reference": provider_reference,
        }

    async def get_status(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "provider_reference": provider_reference,
            "status": "OTP_VERIFICATION_PENDING",
            "is_demo": True,
        }


class AuthorizedAadhaarVerificationProvider(AadhaarVerificationProvider):
    """
    Production implementation connecting to an authorized UIDAI e-KYC / authentication gateway.
    Configured via environment variables (AADHAAR_API_URL, AADHAAR_API_KEY, AADHAAR_CLIENT_ID).
    Never exposes provider secrets or credentials directly in source code.
    """

    provider_name = "AuthorizedAadhaarVerificationProvider (UIDAI e-KYC)"
    is_demo = False

    def __init__(self):
        self.api_url = settings.AADHAAR_API_URL
        self.api_key = settings.AADHAAR_API_KEY
        self.client_id = settings.AADHAAR_CLIENT_ID
        self.client_secret = settings.AADHAAR_CLIENT_SECRET

    async def request_otp(
        self,
        aadhaar_number: str,
        consent_reference: str,
        client_ip: str = "",
    ) -> dict[str, Any]:
        if not self.api_url or not self.api_key:
            # Fallback gracefully with clear message if production credentials are unconfigured
            raise HTTPException(
                status_code=503,
                detail="Aadhaar verification is temporarily unavailable. Please try again later.",
            )
        # Production HTTP request placeholder - standard authorized gateway protocol
        # (In production, an authenticated POST request with encrypted Aadhaar envelope is sent)
        raise HTTPException(
            status_code=503,
            detail="Aadhaar verification is temporarily unavailable. Please try again later.",
        )

    async def verify_otp(
        self,
        provider_reference: str,
        otp: str,
    ) -> dict[str, Any]:
        if not self.api_url or not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="Aadhaar verification is temporarily unavailable. Please try again later.",
            )
        raise HTTPException(
            status_code=503,
            detail="Aadhaar verification is temporarily unavailable. Please try again later.",
        )

    async def resend_otp(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        if not self.api_url or not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="Aadhaar verification is temporarily unavailable. Please try again later.",
            )
        raise HTTPException(
            status_code=503,
            detail="Aadhaar verification is temporarily unavailable. Please try again later.",
        )

    async def cancel(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        return {"success": True, "status": "CANCELLED", "provider_reference": provider_reference}

    async def get_status(
        self,
        provider_reference: str,
    ) -> dict[str, Any]:
        return {"provider": self.provider_name, "provider_reference": provider_reference, "status": "PENDING"}


def get_aadhaar_provider() -> AadhaarVerificationProvider:
    """Factory selecting provider based on configured settings."""
    if settings.AADHAAR_PROVIDER.lower() == "authorized":
        return AuthorizedAadhaarVerificationProvider()
    return MockAadhaarVerificationProvider()


class AadhaarVerificationService:
    """
    High-level business service orchestrating Aadhaar Identity Verification:
    - Validation of format and Verhoeff checksum
    - Privacy protection and tokenization
    - Duplicate citizen account prevention
    - Mandatory consent verification
    - Rate limiting, cooldowns and attempt security
    - Audit logging (without leaking secrets)
    """

    def __init__(self, db: Session):
        self.db = db
        self.provider = get_aadhaar_provider()

    async def record_consent(
        self,
        session_reference: str,
        purpose: str = "identity_verification_citizen_registration",
        policy_version: str = "v1.0",
        consent_given: bool = True,
        ip_address: str = "",
        user_agent: str = "",
    ) -> IdentityVerificationConsent:
        if not consent_given:
            raise HTTPException(status_code=400, detail="Consent is mandatory for Aadhaar identity verification.")

        consent = IdentityVerificationConsent(
            session_reference=session_reference or uuid.uuid4().hex,
            verification_type="aadhaar_otp",
            purpose=purpose,
            policy_version=policy_version,
            consent_given=True,
            consent_timestamp=_utcnow(),
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else "",
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)
        return consent

    async def request_otp(
        self,
        aadhaar_number: str,
        consent_id: int,
        session_reference: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> dict[str, Any]:
        # 1. Format and Verhoeff validation
        is_valid, err_msg = validate_aadhaar_number(aadhaar_number, allow_demo=self.provider.is_demo)
        if not is_valid:
            raise HTTPException(status_code=400, detail=err_msg)

        # 2. Consent verification
        consent = self.db.get(IdentityVerificationConsent, consent_id)
        if not consent or not consent.consent_given:
            raise HTTPException(
                status_code=400,
                detail="A valid mandatory consent record is required before Aadhaar verification can proceed.",
            )

        # 3. Duplicate Citizen Account Check using privacy-preserving token
        aadhaar_token = compute_aadhaar_token(aadhaar_number)
        existing_verified = (
            self.db.query(AadhaarVerification)
            .join(User, AadhaarVerification.user_id == User.id)
            .filter(
                AadhaarVerification.aadhaar_token == aadhaar_token,
                AadhaarVerification.verification_status == "VERIFIED",
                User.is_active == True,  # noqa: E712
            )
            .first()
        )
        if existing_verified:
            # Privacy requirement: Never reveal other account's email, phone, name or address!
            raise HTTPException(
                status_code=409,
                detail="A verified citizen account already exists for this identity. Please use the existing account or contact support.",
            )

        # 4. Invoke provider
        provider_resp = await self.provider.request_otp(
            aadhaar_number=aadhaar_number,
            consent_reference=str(consent.id),
            client_ip=ip_address,
        )

        # 5. Record verification state in database
        last4 = aadhaar_number.replace(" ", "").replace("-", "").strip()[-4:]
        expires_at = _utcnow() + timedelta(seconds=settings.AADHAAR_OTP_EXPIRY_SECONDS)
        cooldown_until = _utcnow() + timedelta(seconds=settings.AADHAAR_RESEND_COOLDOWN_SECONDS)

        verification = AadhaarVerification(
            verification_provider="mock" if self.provider.is_demo else "authorized",
            provider_reference=provider_resp["provider_reference"],
            aadhaar_token=aadhaar_token,
            aadhaar_last4=last4,
            verification_status="OTP_SENT",
            consent_id=consent.id,
            masked_mobile=provider_resp.get("masked_mobile", f"******{last4}"),
            requested_at=_utcnow(),
            expires_at=expires_at,
            attempt_count=0,
            resend_count=0,
            resend_available_at=cooldown_until,
        )
        self.db.add(verification)
        self.db.flush()

        # 6. Audit logging (Sanitized - never log Aadhaar number or OTP)
        AuditLogService.log(
            self.db,
            action="AADHAAR_OTP_REQUESTED",
            entity_type="aadhaar_verification",
            entity_id=str(verification.id),
            details=f"Aadhaar OTP requested. Provider reference: {verification.provider_reference}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        self.db.refresh(verification)

        return {
            "status": "OTP_SENT",
            "verification_id": verification.id,
            "masked_mobile": verification.masked_mobile,
            "masked_aadhaar": mask_aadhaar(aadhaar_number),
            "expires_in_seconds": settings.AADHAAR_OTP_EXPIRY_SECONDS,
            "resend_cooldown_seconds": settings.AADHAAR_RESEND_COOLDOWN_SECONDS,
            "is_demo": self.provider.is_demo,
            "demo_otp": settings.DEMO_AADHAAR_OTP if self.provider.is_demo else None,
            "demo_notice": provider_resp.get("demo_notice") if self.provider.is_demo else None,
        }

    async def verify_otp(
        self,
        verification_id: int,
        otp: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> dict[str, Any]:
        verification = self.db.get(AadhaarVerification, verification_id)
        if not verification:
            raise HTTPException(status_code=404, detail="Aadhaar verification session not found.")

        # Check if already verified
        if verification.verification_status == "VERIFIED":
            return {
                "status": "VERIFIED",
                "verification_id": verification.id,
                "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
                "masked_aadhaar": f"XXXX XXXX {verification.aadhaar_last4}",
            }

        # Check account lock / attempt limits
        if verification.attempt_count >= settings.AADHAAR_MAX_OTP_ATTEMPTS:
            verification.verification_status = "LOCKED"
            self.db.commit()
            AuditLogService.log(
                self.db,
                action="AADHAAR_VERIFICATION_LOCKED",
                entity_type="aadhaar_verification",
                entity_id=str(verification.id),
                details="Aadhaar verification locked due to excessive failed OTP attempts.",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=429,
                detail="Too many verification attempts. Please try again later.",
            )

        # Check expiry
        if verification.expires_at and verification.expires_at.replace(tzinfo=timezone.utc) < _utcnow():
            verification.verification_status = "EXPIRED"
            self.db.commit()
            AuditLogService.log(
                self.db,
                action="AADHAAR_VERIFICATION_EXPIRED",
                entity_type="aadhaar_verification",
                entity_id=str(verification.id),
                details="Aadhaar verification OTP expired.",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=400,
                detail="This OTP has expired. Please request a new OTP.",
            )

        # Validate OTP with provider
        resp = await self.provider.verify_otp(verification.provider_reference, otp.strip())

        if not resp.get("success"):
            verification.attempt_count += 1
            if verification.attempt_count >= settings.AADHAAR_MAX_OTP_ATTEMPTS:
                verification.verification_status = "LOCKED"
            self.db.commit()

            AuditLogService.log(
                self.db,
                action="AADHAAR_OTP_VERIFICATION_FAILED",
                entity_type="aadhaar_verification",
                entity_id=str(verification.id),
                details=f"Failed Aadhaar OTP attempt ({verification.attempt_count}/{settings.AADHAAR_MAX_OTP_ATTEMPTS})",
                ip_address=ip_address,
                user_agent=user_agent,
            )

            error_code = resp.get("error_code")
            if error_code == "EXPIRED_OTP":
                raise HTTPException(status_code=400, detail="This OTP has expired. Please request a new OTP.")
            if error_code == "PROVIDER_ERROR":
                raise HTTPException(
                    status_code=503,
                    detail="Aadhaar verification is temporarily unavailable. Please try again later.",
                )
            if verification.attempt_count >= settings.AADHAAR_MAX_OTP_ATTEMPTS:
                raise HTTPException(
                    status_code=429,
                    detail="Too many verification attempts. Please try again later.",
                )
            raise HTTPException(status_code=400, detail="The OTP entered is incorrect. Please try again.")

        # Verification successful
        verification.verification_status = "VERIFIED"
        verification.verified_at = _utcnow()
        AuditLogService.log(
            self.db,
            action="AADHAAR_VERIFICATION_SUCCESSFUL",
            entity_type="aadhaar_verification",
            entity_id=str(verification.id),
            details=f"Aadhaar identity verified successfully via {self.provider.provider_name}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        self.db.refresh(verification)

        return {
            "status": "VERIFIED",
            "verification_id": verification.id,
            "verified_at": verification.verified_at.isoformat(),
            "masked_aadhaar": f"XXXX XXXX {verification.aadhaar_last4}",
            "provider": self.provider.provider_name,
        }

    async def resend_otp(
        self,
        verification_id: int,
        ip_address: str = "",
        user_agent: str = "",
    ) -> dict[str, Any]:
        verification = self.db.get(AadhaarVerification, verification_id)
        if not verification:
            raise HTTPException(status_code=404, detail="Aadhaar verification session not found.")

        if verification.verification_status == "VERIFIED":
            raise HTTPException(status_code=400, detail="Identity has already been verified.")

        # Check resend limit
        if verification.resend_count >= settings.AADHAAR_MAX_RESEND_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum OTP resend limit ({settings.AADHAAR_MAX_RESEND_ATTEMPTS}) reached. Please restart verification.",
            )

        # Check cooldown
        if verification.resend_available_at and verification.resend_available_at.replace(tzinfo=timezone.utc) > _utcnow():
            remaining = int((verification.resend_available_at.replace(tzinfo=timezone.utc) - _utcnow()).total_seconds())
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before requesting another OTP.",
            )

        # Call provider
        resp = await self.provider.resend_otp(verification.provider_reference)
        if not resp.get("success"):
            raise HTTPException(
                status_code=503,
                detail="Aadhaar verification is temporarily unavailable. Please try again later.",
            )

        verification.resend_count += 1
        verification.expires_at = _utcnow() + timedelta(seconds=settings.AADHAAR_OTP_EXPIRY_SECONDS)
        verification.resend_available_at = _utcnow() + timedelta(seconds=settings.AADHAAR_RESEND_COOLDOWN_SECONDS)
        verification.verification_status = "OTP_SENT"

        AuditLogService.log(
            self.db,
            action="AADHAAR_OTP_RESENT",
            entity_type="aadhaar_verification",
            entity_id=str(verification.id),
            details=f"Aadhaar OTP resent ({verification.resend_count}/{settings.AADHAAR_MAX_RESEND_ATTEMPTS})",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        self.db.refresh(verification)

        return {
            "status": "OTP_SENT",
            "verification_id": verification.id,
            "masked_mobile": verification.masked_mobile,
            "expires_in_seconds": settings.AADHAAR_OTP_EXPIRY_SECONDS,
            "resend_cooldown_seconds": settings.AADHAAR_RESEND_COOLDOWN_SECONDS,
            "resends_remaining": settings.AADHAAR_MAX_RESEND_ATTEMPTS - verification.resend_count,
            "is_demo": self.provider.is_demo,
            "demo_otp": settings.DEMO_AADHAAR_OTP if self.provider.is_demo else None,
        }

    async def cancel(
        self,
        verification_id: int,
        ip_address: str = "",
        user_agent: str = "",
    ) -> dict[str, Any]:
        verification = self.db.get(AadhaarVerification, verification_id)
        if not verification:
            raise HTTPException(status_code=404, detail="Aadhaar verification session not found.")

        if verification.verification_status != "VERIFIED":
            verification.verification_status = "FAILED"
            AuditLogService.log(
                self.db,
                action="AADHAAR_VERIFICATION_CANCELLED",
                entity_type="aadhaar_verification",
                entity_id=str(verification.id),
                details="Aadhaar verification session cancelled by user.",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
        return {"status": "CANCELLED", "verification_id": verification.id}

    async def get_status(self, verification_id: int) -> dict[str, Any]:
        verification = self.db.get(AadhaarVerification, verification_id)
        if not verification:
            raise HTTPException(status_code=404, detail="Aadhaar verification session not found.")

        now = _utcnow()
        seconds_remaining = 0
        if verification.expires_at and verification.expires_at.replace(tzinfo=timezone.utc) > now:
            seconds_remaining = int((verification.expires_at.replace(tzinfo=timezone.utc) - now).total_seconds())

        cooldown_remaining = 0
        if verification.resend_available_at and verification.resend_available_at.replace(tzinfo=timezone.utc) > now:
            cooldown_remaining = int((verification.resend_available_at.replace(tzinfo=timezone.utc) - now).total_seconds())

        return {
            "verification_id": verification.id,
            "verification_status": verification.verification_status,
            "masked_aadhaar": f"XXXX XXXX {verification.aadhaar_last4}",
            "masked_mobile": verification.masked_mobile,
            "provider": verification.verification_provider,
            "attempts_remaining": max(0, settings.AADHAAR_MAX_OTP_ATTEMPTS - verification.attempt_count),
            "resends_remaining": max(0, settings.AADHAAR_MAX_RESEND_ATTEMPTS - verification.resend_count),
            "expires_in_seconds": seconds_remaining,
            "cooldown_remaining_seconds": cooldown_remaining,
            "is_demo": self.provider.is_demo,
        }
