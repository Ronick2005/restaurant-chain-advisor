import json
import datetime
from typing import Dict, List, Optional
import bcrypt
from jose import jwt, JWTError

from utils.config import JWT_SECRET, ROLES

# User database file location
USER_DB_FILE = "users.json"

def get_users() -> Dict:
    """Load users from JSON file."""
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize with default admin user if file doesn't exist
        default_users = {
            "admin": {
                "username": "admin",
                "hashed_password": get_password_hash("admin"),  # Default password: admin
                "role": "admin",
                "full_name": "System Administrator"
            }
        }
        save_users(default_users)
        return default_users

def save_users(users: Dict) -> None:
    """Save users to JSON file."""
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hashed version."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password."""
    users = get_users()
    user = users.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: Dict, expires_delta: Optional[datetime.timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

def create_user(username: str, password: str, role: str, full_name: str) -> bool:
    """Create a new user."""
    if role not in ROLES:
        return False
        
    users = get_users()
    if username in users:
        return False
        
    users[username] = {
        "username": username,
        "hashed_password": get_password_hash(password),
        "role": role,
        "full_name": full_name
    }
    save_users(users)
    return True

def check_permission(user: Dict, resource_type: str, action: str) -> bool:
    """Check if user has permission for a specific action on a resource type."""
    role = user["role"]
    role_permissions = ROLES.get(role, {})
    
    if resource_type == "user_management" and role_permissions.get("user_management"):
        return True
        
    # Check if the action is allowed for the resource type
    allowed_actions = role_permissions.get(f"{resource_type}_access", [])
    if "all" in allowed_actions or action in allowed_actions:
        return True
        
    return False

def has_agent_access(user: Dict, agent_name: str) -> bool:
    """Check if user has access to a specific agent."""
    role = user["role"]
    role_permissions = ROLES.get(role, {})
    
    allowed_agents = role_permissions.get("agent_access", [])
    if "all" in allowed_agents or agent_name in allowed_agents:
        return True
        
    return False

def has_domain_access(user: Dict, domain_name: str) -> bool:
    """Check if user has access to a specific domain specialist."""
    role = user["role"]
    role_permissions = ROLES.get(role, {})
    
    allowed_domains = role_permissions.get("domain_access", [])
    if "all" in allowed_domains or domain_name in allowed_domains:
        return True
        
    return False

def has_memory_access(user: Dict, operation: str) -> bool:
    """Check if user has access to perform an operation on memory."""
    role = user["role"]
    role_permissions = ROLES.get(role, {})
    
    allowed_operations = role_permissions.get("memory_access", [])
    if "all" in allowed_operations or operation in allowed_operations:
        return True
        
    return False
