from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


SECRET_KEY = "expense_tracker_secret_key"
ALGORITHM = "HS256"



# ==========================
# PASSWORD HASH
# ==========================

def hash_password(password: str):

    if not password:
        return None

    password = str(password)

    # bcrypt max 72 bytes
    return pwd_context.hash(
        password[:72]
    )



# ==========================
# PASSWORD VERIFY
# ==========================

def verify_password(
    plain_password: str,
    hashed_password: str
):

    if not plain_password or not hashed_password:
        return False


    try:

        return pwd_context.verify(
            plain_password[:72],
            hashed_password
        )

    except Exception:

        return False




# ==========================
# JWT TOKEN
# ==========================

def create_access_token(data: dict):

    to_encode = data.copy()


    expire = datetime.utcnow() + timedelta(hours=1)


    to_encode.update({
        "exp": expire
    })


    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )




# ==========================
# VERIFY TOKEN
# ==========================

def verify_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload


    except JWTError:

        return None




# ==========================
# GET USER EMAIL
# ==========================

def get_current_user_email(token: str):

    payload = verify_token(token)


    if payload is None:
        return None


    return payload.get("sub")
