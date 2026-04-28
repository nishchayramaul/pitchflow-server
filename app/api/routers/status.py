from fastapi import APIRouter, Depends




router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/status")
def get_status(creator_id : str, = Depends(get_db)) -> dict[str, bool]:
    return check_slug_availability(db, slug)