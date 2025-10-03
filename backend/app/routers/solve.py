from fastapi import APIRouter, Query
router = APIRouter(prefix="/solve", tags=["solve"])

@router.get("/preview")
def preview_stub(post_id: int = Query(...), month: int = Query(...), year: int = Query(...)):
    # Wire the real Solver once ActivityProvider and DB glue are in place.
    return {
        "ok": True,
        "note": "Stub response. Implement Solver.preview_month(...) and wire here.",
        "input": {"post_id": post_id, "month": month, "year": year}
    }
