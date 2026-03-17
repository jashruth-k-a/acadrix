from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from bson import ObjectId
from database import get_users_collection
from models import UserRegister, UserLogin, TokenResponse, UserOut
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister):
    users = get_users_collection()

    # Check duplicate email
    if await users.find_one({"email": body.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user document
    now = datetime.now(timezone.utc)
    user_doc = {
        "name": body.name,
        "email": body.email,
        "password": hash_password(body.password),
        "created_at": now,
    }
    result = await users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Issue token
    token = create_access_token({"sub": user_id, "email": body.email})

    return TokenResponse(
        access_token=token,
        user=UserOut(id=user_id, name=body.name, email=body.email, created_at=now),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    users = get_users_collection()

    user = await users.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token({"sub": user_id, "email": user["email"]})

    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user_id,
            name=user["name"],
            email=user["email"],
            created_at=user["created_at"],
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    users = get_users_collection()
    user = await users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )