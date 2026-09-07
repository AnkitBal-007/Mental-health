"""
Temporary Admin Router for Remote Cloud Deployment Bootstrapping.

NOTE: This router provides a temporary admin-only endpoint to seed demo data
into remote cloud databases (e.g., Supabase PostgreSQL) after deployment,
without requiring SSH/CLI access to the database.

IMPORTANT: THIS ENDPOINT AND FILE SHOULD BE REMOVED BEFORE FINAL SUBMISSION.
"""

import logging
from fastapi import APIRouter, Header, HTTPException, status
from config import ADMIN_SEED_TOKEN
from seed_data import seed_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin (Temporary Demo Seeder)"])


@router.post("/seed-demo-data")
def trigger_seed_demo_data(
    x_admin_seed_token: str = Header(
        ...,
        alias="X-Admin-Seed-Token",
        description="Secret token matching the ADMIN_SEED_TOKEN environment variable."
    )
):
    """
    Temporary endpoint to seed synthetic demo data (users, victims, check-ins, alerts)
    into whatever database the backend is currently connected to.

    Protected by the ADMIN_SEED_TOKEN environment variable.

    IMPORTANT: Remove this endpoint before final hackathon submission.
    """
    if not ADMIN_SEED_TOKEN:
        logger.error("ADMIN_SEED_TOKEN is not configured in backend environment.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_SEED_TOKEN environment variable is not configured on the backend server."
        )

    if x_admin_seed_token != ADMIN_SEED_TOKEN:
        logger.warning("Unauthorized attempt to access /admin/seed-demo-data with invalid token.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid X-Admin-Seed-Token header."
        )

    try:
        logger.info("Admin seed triggered via /admin/seed-demo-data. Executing seeder...")
        result = seed_database()
        return {
            "status": "success",
            "message": "Demo data successfully seeded into connected database.",
            "details": result or {},
            "demo_accounts": [
                {"role": "national", "username": "national_admin"},
                {"role": "state", "username": "state_bihar"},
                {"role": "district", "username": "district_patna"},
                {"role": "counsellor", "username": "counsellor_priya"},
            ]
        }
    except Exception as e:
        logger.error("Error executing seed_database: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed demo data: {str(e)}"
        )
