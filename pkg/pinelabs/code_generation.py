"""
Pine Labs Code Generation MCP tools.

Provides two developer-facing tools:
1. ``detect_stack`` — Detect the technology stack of a project based on
   file information.  Returns language, framework, frontend framework,
   and package manager.
2. ``integrate_pinelabs_checkout`` — Generate complete Pine Labs checkout
   integration code for a detected stack.  Returns backend routes,
   frontend code, dependencies, environment variables, and AI
   instructions.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

from fastmcp import FastMCP

logger = logging.getLogger("pinelabs-mcp-server.code_generation")

# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------


@dataclass
class EditItem:
    line: str
    add: str
    why: str


@dataclass
class FileAction:
    action: str          # "create", "manual_edit"
    path: str
    code: str = ""
    description: str = ""
    edits: list[EditItem] = field(default_factory=list)


@dataclass
class Dependency:
    name: str
    install_command: str


@dataclass
class EnvVar:
    name: str
    value: str


@dataclass
class IntegrateCheckoutOutput:
    summary: str
    files: list[FileAction]
    dependencies: list[Dependency]
    env_vars: list[EnvVar]
    test_instructions: str
    ai_instructions: str


@dataclass
class DetectStackOutput:
    language: str
    framework: str
    frontend: str
    package_manager: str
    is_full_stack: bool
    confidence: float
    notes: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _contains(haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


def _has_suffix(files: list[str], suffix: str) -> bool:
    return any(f.endswith(suffix) for f in files)


def _has_path(files: list[str], path: str) -> bool:
    return any(f == path or f.endswith("/" + path) for f in files)


# ---------------------------------------------------------------------------
# Stack detection logic
# ---------------------------------------------------------------------------

def _detect_project_stack(
    files: list[str],
    package_json: Optional[dict],
    requirements_txt: str,
    go_mod: str,
    pubspec_yaml: str,
) -> DetectStackOutput:
    """Detect the project technology stack from files and dependency info."""

    notes: list[str] = []

    # Flutter
    if pubspec_yaml or _has_suffix(files, "pubspec.yaml"):
        return DetectStackOutput(
            language="dart",
            framework="flutter",
            frontend="",
            package_manager="pub",
            is_full_stack=False,
            confidence=0.95,
            notes=["Flutter mobile app detected"],
        )

    # Go
    if go_mod or _has_suffix(files, "go.mod"):
        framework = "gin"
        if _contains(go_mod, "github.com/labstack/echo"):
            framework = "echo"
        elif _contains(go_mod, "github.com/gofiber/fiber"):
            framework = "fiber"
        return DetectStackOutput(
            language="go",
            framework=framework,
            frontend="",
            package_manager="go-mod",
            is_full_stack=True,
            confidence=0.9,
            notes=["Go project with " + framework],
        )

    # Rust
    if _has_suffix(files, "Cargo.toml"):
        return DetectStackOutput(
            language="rust",
            framework="actix",
            frontend="",
            package_manager="cargo",
            is_full_stack=True,
            confidence=0.9,
            notes=["Rust project detected"],
        )

    # Java / Spring
    if _has_suffix(files, "pom.xml") or _has_suffix(files, "build.gradle"):
        return DetectStackOutput(
            language="java",
            framework="spring",
            frontend="",
            package_manager="maven",
            is_full_stack=True,
            confidence=0.85,
            notes=["Java project detected — assuming Spring Boot"],
        )

    # PHP / Laravel
    if _has_suffix(files, "composer.json"):
        return DetectStackOutput(
            language="php",
            framework="laravel",
            frontend="",
            package_manager="composer",
            is_full_stack=True,
            confidence=0.85,
            notes=["PHP project detected"],
        )

    # Ruby / Rails
    if _has_suffix(files, "Gemfile"):
        return DetectStackOutput(
            language="ruby",
            framework="rails",
            frontend="",
            package_manager="bundler",
            is_full_stack=True,
            confidence=0.85,
            notes=["Ruby project detected"],
        )

    # .NET
    if _has_suffix(files, ".csproj") or _has_suffix(files, ".sln"):
        return DetectStackOutput(
            language="csharp",
            framework="aspnet",
            frontend="",
            package_manager="nuget",
            is_full_stack=True,
            confidence=0.85,
            notes=[".NET project detected — assuming ASP.NET Core"],
        )

    # Python
    if (
        requirements_txt
        or _has_suffix(files, "requirements.txt")
        or _has_suffix(files, "pyproject.toml")
    ):
        framework = "flask"
        for fw in ("django", "flask", "fastapi", "starlette"):
            if _contains(requirements_txt, fw):
                framework = fw
                break
        if _has_path(files, "manage.py"):
            framework = "django"
        return DetectStackOutput(
            language="python",
            framework=framework,
            frontend="",
            package_manager="pip",
            is_full_stack=True,
            confidence=0.85,
            notes=["Python project with " + framework],
        )

    # Node.js / TypeScript
    if package_json is not None or _has_suffix(files, "package.json"):
        deps: dict[str, bool] = {}
        if package_json:
            for section in ("dependencies", "devDependencies"):
                if isinstance(package_json.get(section), dict):
                    for k in package_json[section]:
                        deps[k] = True

        is_ts = _has_suffix(files, "tsconfig.json") or "typescript" in deps
        language = "typescript" if is_ts else "javascript"

        # Package manager
        pkg_mgr = "npm"
        if _has_path(files, "yarn.lock"):
            pkg_mgr = "yarn"
        elif _has_path(files, "pnpm-lock.yaml"):
            pkg_mgr = "pnpm"
        elif _has_path(files, "bun.lockb"):
            pkg_mgr = "bun"

        # Backend framework
        framework = "express"
        node_fws = {
            "next": "nextjs",
            "express": "express",
            "fastify": "fastify",
            "koa": "koa",
            "hono": "hono",
            "nuxt": "nuxt",
            "@nestjs/core": "nestjs",
        }
        for pkg, fw in node_fws.items():
            if pkg in deps:
                framework = fw
                notes.append("Found " + pkg + " in dependencies")
                break

        # Frontend framework
        frontend = ""
        fe_fws = {
            "react": "react",
            "vue": "vue",
            "@angular/core": "angular",
            "svelte": "svelte",
            "solid-js": "solid",
            "react-native": "react-native",
            "expo": "react-native",
        }
        for pkg, fw in fe_fws.items():
            if pkg in deps:
                frontend = fw
                notes.append("Found " + pkg + " for frontend")
                break

        if frontend == "react-native":
            return DetectStackOutput(
                language=language,
                framework="react-native",
                frontend="",
                package_manager=pkg_mgr,
                is_full_stack=False,
                confidence=0.95,
                notes=["React Native mobile app detected"],
            )

        is_full = framework in ("nextjs", "nuxt", "nestjs") or (
            framework != "node" and frontend == ""
        )

        return DetectStackOutput(
            language=language,
            framework=framework,
            frontend=frontend,
            package_manager=pkg_mgr,
            is_full_stack=is_full,
            confidence=0.9,
            notes=notes,
        )

    # Fallback
    return DetectStackOutput(
        language="unknown",
        framework="unknown",
        frontend="",
        package_manager="unknown",
        is_full_stack=False,
        confidence=0.1,
        notes=["Could not detect project stack"],
    )


# ===================================================================
# PINE LABS CHECKOUT — backend templates
# ===================================================================

_PINELABS_CLIENT_ID_PLACEHOLDER = "YOUR_PINELABS_CLIENT_ID"
_PINELABS_CLIENT_SECRET_PLACEHOLDER = "YOUR_PINELABS_CLIENT_SECRET"

_TEST_INSTRUCTIONS = (
    "Use the Pine Labs UAT sandbox for testing.\n"
    "UAT base URL: https://pluraluat.v2.pinepg.in/api\n"
    "Test card: 4012 0010 3714 1112, Expiry: 12/25, CVV: 212\n"
    "Test UPI VPA: success@upi\n"
    "Amounts are in paisa (100 paisa = Rs.1)."
)

_ENV_VARS = [
    EnvVar(
        name="PINELABS_CLIENT_ID",
        value=_PINELABS_CLIENT_ID_PLACEHOLDER,
    ),
    EnvVar(
        name="PINELABS_CLIENT_SECRET",
        value=_PINELABS_CLIENT_SECRET_PLACEHOLDER,
    ),
    EnvVar(
        name="PINELABS_BASE_URL",
        value="https://pluraluat.v2.pinepg.in/api",
    ),
]


def _next_steps_file() -> FileAction:
    return FileAction(
        action="create",
        path="NEXT_STEPS.md",
        description=(
            "Setup guide — add your Pine Labs credentials and test"
        ),
        code="""\
# Next Steps — Pine Labs Checkout Integration

## 1. Add Your Pine Labs API Credentials

Open the `.env` file in your project root and replace the placeholder values:

```
PINELABS_CLIENT_ID=your_actual_client_id
PINELABS_CLIENT_SECRET=your_actual_client_secret
```

### Where to find your credentials

1. Log in to the [Plural Dashboard](https://dashboard.pluralonline.com/)
2. Navigate to **Developer** → **API Keys**
3. Copy your **Client ID** and **Client Secret**
4. For testing, use **UAT/Sandbox** keys

## 2. Test the Integration

After adding your credentials, start your development server and test:

### Test Card
| Field       | Value              |
|-------------|--------------------|
| Card Number | 4012 0010 3714 1112 |
| Expiry      | 12/25              |
| CVV         | 212                |

### Test UPI
| Field | Value         |
|-------|---------------|
| VPA   | success@upi   |

## 3. Go Live

When ready for production:

1. Switch to **Live Mode** on the Plural Dashboard
2. Generate **Live** API keys
3. Update `.env`:
   - `PINELABS_BASE_URL=https://api.pluralpay.in/api`
   - Replace test keys with live keys
4. Ensure your server is running over HTTPS
""",
    )


def _ai_instructions_suffix() -> str:
    return """

**AFTER APPLYING ALL FILES — YOU MUST DO THIS:**
1. Create the NEXT_STEPS.md file in the project root
2. OPEN the NEXT_STEPS.md file in the user's IDE/editor
3. Tell the user the integration is complete and they need to add \
their Pine Labs credentials as shown in NEXT_STEPS.md
"""


# ---------------------------------------------------------------
# Django
# ---------------------------------------------------------------

def _get_django_integration(
    frontend_code: str,
    frontend_file: str,
    frontend_desc: str,
) -> IntegrateCheckoutOutput:
    views_code = '''\
import hashlib
import hmac
import json
import os
import time

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def _get_token():
    """Fetch an access token from Pine Labs token endpoint."""
    resp = requests.post(
        f"{settings.PINELABS_BASE_URL}/auth/v1/token",
        json={
            "client_id": settings.PINELABS_CLIENT_ID,
            "client_secret": settings.PINELABS_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@csrf_exempt
@require_POST
def create_order(request):
    """Create a Pine Labs checkout order and return the redirect URL."""
    try:
        data = json.loads(request.body)
        amount = data.get("amount", 0)
        if amount <= 0:
            return JsonResponse(
                {"success": False, "error": "Invalid amount"}, status=400,
            )

        token = _get_token()
        order_resp = requests.post(
            f"{settings.PINELABS_BASE_URL}/checkout/v1/orders",
            json={
                "merchant_order_reference": f"order_{int(time.time())}",
                "order_amount": {
                    "value": int(amount),
                    "currency": data.get("currency", "INR"),
                },
                "callback_url": data.get(
                    "callback_url",
                    request.build_absolute_uri("/api/pinelabs/callback"),
                ),
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        order_resp.raise_for_status()
        order = order_resp.json()

        return JsonResponse({
            "success": True,
            "order_id": order.get("order_id"),
            "redirect_url": order.get("redirect_url"),
            "token": order.get("token"),
        })
    except Exception as exc:
        return JsonResponse(
            {"success": False, "error": str(exc)}, status=500,
        )


@csrf_exempt
@require_POST
def callback(request):
    """Handle Pine Labs payment callback."""
    try:
        data = json.loads(request.body) if request.body else dict(request.POST)
        order_id = data.get("order_id") or data.get("plural_order_id")
        return JsonResponse({
            "success": True,
            "message": "Payment callback received",
            "order_id": order_id,
        })
    except Exception as exc:
        return JsonResponse(
            {"success": False, "error": str(exc)}, status=500,
        )
'''

    urls_code = '''\
from django.urls import path

from . import views

urlpatterns = [
    path("order", views.create_order, name="pinelabs_order"),
    path("callback", views.callback, name="pinelabs_callback"),
]
'''

    return IntegrateCheckoutOutput(
        summary=(
            "Complete Pine Labs checkout integration for Django"
        ),
        files=[
            FileAction(
                action="create",
                path="pinelabs_payments/__init__.py",
                code="",
                description="Django app init file",
            ),
            FileAction(
                action="create",
                path="pinelabs_payments/views.py",
                code=views_code,
                description="Django views — create order + callback",
            ),
            FileAction(
                action="create",
                path="pinelabs_payments/urls.py",
                code=urls_code,
                description="Django URL patterns for Pine Labs",
            ),
            FileAction(
                action="create",
                path=frontend_file,
                code=frontend_code,
                description=frontend_desc,
            ),
            FileAction(
                action="manual_edit",
                path="settings.py",
                description="Add to settings.py",
                edits=[
                    EditItem(
                        line="In INSTALLED_APPS list",
                        add="'pinelabs_payments',",
                        why="Register the Pine Labs app",
                    ),
                    EditItem(
                        line="After other settings",
                        add=(
                            "PINELABS_CLIENT_ID = "
                            "os.environ.get('PINELABS_CLIENT_ID')"
                        ),
                        why="Pine Labs client ID",
                    ),
                    EditItem(
                        line="After PINELABS_CLIENT_ID",
                        add=(
                            "PINELABS_CLIENT_SECRET = "
                            "os.environ.get('PINELABS_CLIENT_SECRET')"
                        ),
                        why="Pine Labs client secret",
                    ),
                    EditItem(
                        line="After PINELABS_CLIENT_SECRET",
                        add=(
                            "PINELABS_BASE_URL = "
                            "os.environ.get('PINELABS_BASE_URL', "
                            "'https://pluraluat.v2.pinepg.in/api')"
                        ),
                        why="Pine Labs API base URL",
                    ),
                ],
            ),
            FileAction(
                action="manual_edit",
                path="urls.py",
                description="Add to main urls.py",
                edits=[
                    EditItem(
                        line="In urlpatterns",
                        add=(
                            "path('api/pinelabs/', "
                            "include('pinelabs_payments.urls')),"
                        ),
                        why="Mount Pine Labs URLs",
                    ),
                ],
            ),
            _next_steps_file(),
        ],
        dependencies=[
            Dependency(
                name="requests",
                install_command="pip install requests",
            ),
        ],
        env_vars=list(_ENV_VARS),
        test_instructions=_TEST_INSTRUCTIONS,
        ai_instructions=_ai_instructions_suffix(),
    )


# ---------------------------------------------------------------
# Flask
# ---------------------------------------------------------------

def _get_flask_integration(
    frontend_code: str,
    frontend_file: str,
    frontend_desc: str,
) -> IntegrateCheckoutOutput:
    app_code = '''\
import os
import time

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

app = Flask(__name__)

BASE_URL = os.environ.get(
    "PINELABS_BASE_URL", "https://pluraluat.v2.pinepg.in/api",
)
CLIENT_ID = os.environ.get("PINELABS_CLIENT_ID")
CLIENT_SECRET = os.environ.get("PINELABS_CLIENT_SECRET")


def _get_token():
    resp = requests.post(
        f"{BASE_URL}/auth/v1/token",
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@app.post("/api/pinelabs/order")
def create_order():
    data = request.get_json()
    amount = data.get("amount", 0)
    if amount <= 0:
        return jsonify(success=False, error="Invalid amount"), 400

    try:
        token = _get_token()
        order_resp = requests.post(
            f"{BASE_URL}/checkout/v1/orders",
            json={
                "merchant_order_reference": f"order_{int(time.time())}",
                "order_amount": {
                    "value": int(amount),
                    "currency": data.get("currency", "INR"),
                },
                "callback_url": data.get("callback_url", "/api/pinelabs/callback"),
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        order_resp.raise_for_status()
        order = order_resp.json()
        return jsonify(
            success=True,
            order_id=order.get("order_id"),
            redirect_url=order.get("redirect_url"),
            token=order.get("token"),
        )
    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 500


@app.post("/api/pinelabs/callback")
def callback():
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id") or data.get("plural_order_id")
    return jsonify(
        success=True,
        message="Payment callback received",
        order_id=order_id,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
'''

    return IntegrateCheckoutOutput(
        summary="Complete Pine Labs checkout integration for Flask",
        files=[
            FileAction(
                action="create",
                path="pinelabs_routes.py",
                code=app_code,
                description="Flask routes — create order + callback",
            ),
            FileAction(
                action="create",
                path=frontend_file,
                code=frontend_code,
                description=frontend_desc,
            ),
            _next_steps_file(),
        ],
        dependencies=[
            Dependency(name="requests", install_command="pip install requests"),
            Dependency(
                name="python-dotenv",
                install_command="pip install python-dotenv",
            ),
        ],
        env_vars=list(_ENV_VARS),
        test_instructions=_TEST_INSTRUCTIONS,
        ai_instructions=_ai_instructions_suffix(),
    )


# ---------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------

def _get_fastapi_integration(
    frontend_code: str,
    frontend_file: str,
    frontend_desc: str,
) -> IntegrateCheckoutOutput:
    router_code = '''\
import os
import time

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

load_dotenv()

router = APIRouter(prefix="/api/pinelabs")

BASE_URL = os.environ.get(
    "PINELABS_BASE_URL", "https://pluraluat.v2.pinepg.in/api",
)
CLIENT_ID = os.environ.get("PINELABS_CLIENT_ID")
CLIENT_SECRET = os.environ.get("PINELABS_CLIENT_SECRET")


class OrderRequest(BaseModel):
    amount: int
    currency: str = "INR"
    callback_url: str | None = None


async def _get_token() -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{BASE_URL}/auth/v1/token",
            json={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


@router.post("/order")
async def create_order(req: OrderRequest):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    token = await _get_token()
    async with httpx.AsyncClient(timeout=15) as client:
        order_resp = await client.post(
            f"{BASE_URL}/checkout/v1/orders",
            json={
                "merchant_order_reference": f"order_{int(time.time())}",
                "order_amount": {
                    "value": req.amount,
                    "currency": req.currency,
                },
                "callback_url": req.callback_url or "/api/pinelabs/callback",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        order_resp.raise_for_status()
        order = order_resp.json()
    return {
        "success": True,
        "order_id": order.get("order_id"),
        "redirect_url": order.get("redirect_url"),
        "token": order.get("token"),
    }


@router.post("/callback")
async def callback(data: dict | None = None):
    data = data or {}
    order_id = data.get("order_id") or data.get("plural_order_id")
    return {
        "success": True,
        "message": "Payment callback received",
        "order_id": order_id,
    }
'''

    return IntegrateCheckoutOutput(
        summary="Complete Pine Labs checkout integration for FastAPI",
        files=[
            FileAction(
                action="create",
                path="pinelabs_router.py",
                code=router_code,
                description="FastAPI router — create order + callback",
            ),
            FileAction(
                action="manual_edit",
                path="main.py",
                description="Include the router in your FastAPI app",
                edits=[
                    EditItem(
                        line="After app = FastAPI(...)",
                        add=(
                            "from pinelabs_router import router as "
                            "pinelabs_router\n"
                            "app.include_router(pinelabs_router)"
                        ),
                        why="Mount Pine Labs routes",
                    ),
                ],
            ),
            FileAction(
                action="create",
                path=frontend_file,
                code=frontend_code,
                description=frontend_desc,
            ),
            _next_steps_file(),
        ],
        dependencies=[
            Dependency(name="httpx", install_command="pip install httpx"),
            Dependency(
                name="python-dotenv",
                install_command="pip install python-dotenv",
            ),
        ],
        env_vars=list(_ENV_VARS),
        test_instructions=_TEST_INSTRUCTIONS,
        ai_instructions=_ai_instructions_suffix(),
    )


# ---------------------------------------------------------------
# Express (Node.js)
# ---------------------------------------------------------------

def _get_express_integration(
    frontend_code: str,
    frontend_file: str,
    frontend_desc: str,
) -> IntegrateCheckoutOutput:
    routes_code = '''\
const express = require("express");
const router = express.Router();

const BASE_URL =
  process.env.PINELABS_BASE_URL ||
  "https://pluraluat.v2.pinepg.in/api";
const CLIENT_ID = process.env.PINELABS_CLIENT_ID;
const CLIENT_SECRET = process.env.PINELABS_CLIENT_SECRET;

async function getToken() {
  const res = await fetch(`${BASE_URL}/auth/v1/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      grant_type: "client_credentials",
    }),
  });
  if (!res.ok) throw new Error("Token fetch failed");
  const data = await res.json();
  return data.access_token;
}

router.post("/order", async (req, res) => {
  try {
    const { amount, currency = "INR", callback_url } = req.body;
    if (!amount || amount <= 0) {
      return res.status(400).json({ success: false, error: "Invalid amount" });
    }

    const token = await getToken();
    const orderRes = await fetch(`${BASE_URL}/checkout/v1/orders`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        merchant_order_reference: `order_${Date.now()}`,
        order_amount: { value: amount, currency },
        callback_url: callback_url || "/api/pinelabs/callback",
      }),
    });

    if (!orderRes.ok) {
      const err = await orderRes.text();
      throw new Error(err);
    }
    const order = await orderRes.json();

    res.json({
      success: true,
      order_id: order.order_id,
      redirect_url: order.redirect_url,
      token: order.token,
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

router.post("/callback", (req, res) => {
  const orderId = req.body.order_id || req.body.plural_order_id;
  res.json({
    success: true,
    message: "Payment callback received",
    order_id: orderId,
  });
});

module.exports = router;
'''

    return IntegrateCheckoutOutput(
        summary="Complete Pine Labs checkout integration for Express",
        files=[
            FileAction(
                action="create",
                path="routes/pinelabs.js",
                code=routes_code,
                description="Express routes — create order + callback",
            ),
            FileAction(
                action="manual_edit",
                path="app.js",
                description="Mount Pine Labs routes in your Express app",
                edits=[
                    EditItem(
                        line="After other app.use() calls",
                        add=(
                            'const pinelabsRoutes = '
                            'require("./routes/pinelabs");\n'
                            'app.use("/api/pinelabs", pinelabsRoutes);'
                        ),
                        why="Mount Pine Labs routes",
                    ),
                ],
            ),
            FileAction(
                action="create",
                path=frontend_file,
                code=frontend_code,
                description=frontend_desc,
            ),
            _next_steps_file(),
        ],
        dependencies=[
            Dependency(
                name="dotenv",
                install_command="npm install dotenv",
            ),
        ],
        env_vars=list(_ENV_VARS),
        test_instructions=_TEST_INSTRUCTIONS,
        ai_instructions=_ai_instructions_suffix(),
    )


# ---------------------------------------------------------------
# Next.js
# ---------------------------------------------------------------

def _get_nextjs_integration() -> IntegrateCheckoutOutput:
    route_code = '''\
import { NextResponse } from "next/server";

const BASE_URL =
  process.env.PINELABS_BASE_URL ||
  "https://pluraluat.v2.pinepg.in/api";

async function getToken() {
  const res = await fetch(`${BASE_URL}/auth/v1/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: process.env.PINELABS_CLIENT_ID,
      client_secret: process.env.PINELABS_CLIENT_SECRET,
      grant_type: "client_credentials",
    }),
  });
  if (!res.ok) throw new Error("Token fetch failed");
  return (await res.json()).access_token;
}

export async function POST(request) {
  try {
    const { amount, currency = "INR", callback_url } = await request.json();
    if (!amount || amount <= 0) {
      return NextResponse.json(
        { success: false, error: "Invalid amount" },
        { status: 400 },
      );
    }

    const token = await getToken();
    const orderRes = await fetch(`${BASE_URL}/checkout/v1/orders`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        merchant_order_reference: `order_${Date.now()}`,
        order_amount: { value: amount, currency },
        callback_url: callback_url || "/api/pinelabs/callback",
      }),
    });
    if (!orderRes.ok) throw new Error(await orderRes.text());
    const order = await orderRes.json();

    return NextResponse.json({
      success: true,
      order_id: order.order_id,
      redirect_url: order.redirect_url,
      token: order.token,
    });
  } catch (err) {
    return NextResponse.json(
      { success: false, error: err.message },
      { status: 500 },
    );
  }
}
'''

    callback_code = '''\
import { NextResponse } from "next/server";

export async function POST(request) {
  const data = await request.json().catch(() => ({}));
  const orderId = data.order_id || data.plural_order_id;
  return NextResponse.json({
    success: true,
    message: "Payment callback received",
    order_id: orderId,
  });
}
'''

    component_code = '''\
"use client";

import { useState } from "react";

export default function PinelabsCheckout({ amount }) {
  const [loading, setLoading] = useState(false);

  const handlePayment = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/pinelabs/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      // Redirect to Pine Labs checkout page
      window.location.href = data.redirect_url;
    } catch (err) {
      alert("Payment failed: " + err.message);
      setLoading(false);
    }
  };

  return (
    <button onClick={handlePayment} disabled={loading}>
      {loading ? "Processing..." : "Pay with Pine Labs"}
    </button>
  );
}
'''

    return IntegrateCheckoutOutput(
        summary=(
            "Complete Pine Labs checkout integration for Next.js "
            "(App Router)"
        ),
        files=[
            FileAction(
                action="create",
                path="app/api/pinelabs/order/route.js",
                code=route_code,
                description="Next.js API route — create order",
            ),
            FileAction(
                action="create",
                path="app/api/pinelabs/callback/route.js",
                code=callback_code,
                description="Next.js API route — payment callback",
            ),
            FileAction(
                action="create",
                path="components/PinelabsCheckout.jsx",
                code=component_code,
                description="React component for Pine Labs checkout",
            ),
            _next_steps_file(),
        ],
        dependencies=[],
        env_vars=list(_ENV_VARS),
        test_instructions=_TEST_INSTRUCTIONS,
        ai_instructions=_ai_instructions_suffix(),
    )


# ---------------------------------------------------------------
# Gin (Go)
# ---------------------------------------------------------------

def _get_gin_integration(
    frontend_code: str,
    frontend_file: str,
    frontend_desc: str,
) -> IntegrateCheckoutOutput:
    handler_code = '''\
package pinelabs

import (
\t"bytes"
\t"encoding/json"
\t"fmt"
\t"io"
\t"net/http"
\t"os"
\t"time"

\t"github.com/gin-gonic/gin"
)

var (
\tbaseURL      = envOrDefault("PINELABS_BASE_URL", "https://pluraluat.v2.pinepg.in/api")
\tclientID     = os.Getenv("PINELABS_CLIENT_ID")
\tclientSecret = os.Getenv("PINELABS_CLIENT_SECRET")
)

func envOrDefault(key, fallback string) string {
\tif v := os.Getenv(key); v != "" {
\t\treturn v
\t}
\treturn fallback
}

func getToken() (string, error) {
\tbody, _ := json.Marshal(map[string]string{
\t\t"client_id":     clientID,
\t\t"client_secret": clientSecret,
\t\t"grant_type":    "client_credentials",
\t})
\tresp, err := http.Post(
\t\tbaseURL+"/auth/v1/token",
\t\t"application/json",
\t\tbytes.NewReader(body),
\t)
\tif err != nil {
\t\treturn "", err
\t}
\tdefer resp.Body.Close()
\tvar result map[string]interface{}
\tif err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
\t\treturn "", err
\t}
\ttok, _ := result["access_token"].(string)
\tif tok == "" {
\t\treturn "", fmt.Errorf("empty token")
\t}
\treturn tok, nil
}

func RegisterRoutes(r *gin.Engine) {
\tapi := r.Group("/api/pinelabs")
\tapi.POST("/order", createOrder)
\tapi.POST("/callback", callback)
}

func createOrder(c *gin.Context) {
\tvar req struct {
\t\tAmount      int    `json:"amount"`
\t\tCurrency    string `json:"currency"`
\t\tCallbackURL string `json:"callback_url"`
\t}
\tif err := c.ShouldBindJSON(&req); err != nil {
\t\tc.JSON(400, gin.H{"success": false, "error": err.Error()})
\t\treturn
\t}
\tif req.Amount <= 0 {
\t\tc.JSON(400, gin.H{"success": false, "error": "Invalid amount"})
\t\treturn
\t}
\tif req.Currency == "" {
\t\treq.Currency = "INR"
\t}

\ttoken, err := getToken()
\tif err != nil {
\t\tc.JSON(500, gin.H{"success": false, "error": err.Error()})
\t\treturn
\t}

\torderBody, _ := json.Marshal(map[string]interface{}{
\t\t"merchant_order_reference": fmt.Sprintf("order_%d", time.Now().Unix()),
\t\t"order_amount": map[string]interface{}{
\t\t\t"value":    req.Amount,
\t\t\t"currency": req.Currency,
\t\t},
\t\t"callback_url": req.CallbackURL,
\t})

\thttpReq, _ := http.NewRequest(
\t\t"POST",
\t\tbaseURL+"/checkout/v1/orders",
\t\tbytes.NewReader(orderBody),
\t)
\thttpReq.Header.Set("Content-Type", "application/json")
\thttpReq.Header.Set("Authorization", "Bearer "+token)

\tresp, err := http.DefaultClient.Do(httpReq)
\tif err != nil {
\t\tc.JSON(500, gin.H{"success": false, "error": err.Error()})
\t\treturn
\t}
\tdefer resp.Body.Close()
\trespBody, _ := io.ReadAll(resp.Body)

\tvar order map[string]interface{}
\tjson.Unmarshal(respBody, &order)

\tc.JSON(200, gin.H{
\t\t"success":      true,
\t\t"order_id":     order["order_id"],
\t\t"redirect_url": order["redirect_url"],
\t\t"token":        order["token"],
\t})
}

func callback(c *gin.Context) {
\tvar data map[string]interface{}
\tc.ShouldBindJSON(&data)
\torderID := data["order_id"]
\tif orderID == nil {
\t\torderID = data["plural_order_id"]
\t}
\tc.JSON(200, gin.H{
\t\t"success":  true,
\t\t"message":  "Payment callback received",
\t\t"order_id": orderID,
\t})
}
'''

    return IntegrateCheckoutOutput(
        summary="Complete Pine Labs checkout integration for Go/Gin",
        files=[
            FileAction(
                action="create",
                path="pinelabs/handler.go",
                code=handler_code,
                description="Gin handlers — create order + callback",
            ),
            FileAction(
                action="manual_edit",
                path="main.go",
                description="Register Pine Labs routes in main.go",
                edits=[
                    EditItem(
                        line="After router := gin.Default()",
                        add='pinelabs.RegisterRoutes(router)',
                        why="Mount Pine Labs routes",
                    ),
                ],
            ),
            FileAction(
                action="create",
                path=frontend_file,
                code=frontend_code,
                description=frontend_desc,
            ),
            _next_steps_file(),
        ],
        dependencies=[
            Dependency(
                name="gin",
                install_command="go get github.com/gin-gonic/gin",
            ),
        ],
        env_vars=list(_ENV_VARS),
        test_instructions=_TEST_INSTRUCTIONS,
        ai_instructions=_ai_instructions_suffix(),
    )


# ===================================================================
# FRONTEND TEMPLATES
# ===================================================================

def _get_vanilla_frontend() -> tuple[str, str, str]:
    """Return (code, filename, description) for vanilla JS frontend."""
    code = '''\
/**
 * Pine Labs Payment Integration — Vanilla JS
 * Redirects customer to Pine Labs hosted checkout page.
 */
async function initiatePinelabsPayment(amount, options = {}) {
  try {
    const res = await fetch("/api/pinelabs/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        amount,
        currency: options.currency || "INR",
        callback_url: options.callbackUrl,
      }),
    });

    const data = await res.json();
    if (!data.success) throw new Error(data.error || "Failed to create order");

    // Redirect to Pine Labs checkout
    window.location.href = data.redirect_url;
  } catch (error) {
    console.error("Payment failed:", error);
    if (options.onError) options.onError(error);
  }
}
'''
    return code, "public/js/pinelabs.js", "Vanilla JS Pine Labs payment helper"


def _get_react_frontend() -> tuple[str, str, str]:
    """Return (code, filename, description) for React frontend."""
    code = '''\
import { useState } from "react";

export function usePinelabs() {
  const [loading, setLoading] = useState(false);

  const pay = async (amount, options = {}) => {
    if (loading) return;
    setLoading(true);
    try {
      const res = await fetch("/api/pinelabs/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount,
          currency: options.currency || "INR",
          callback_url: options.callbackUrl,
        }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      // Redirect to Pine Labs checkout
      window.location.href = data.redirect_url;
    } catch (err) {
      options.onError?.(err);
      setLoading(false);
    }
  };

  return { pay, loading };
}

export function PinelabsButton({ amount, onError, children }) {
  const { pay, loading } = usePinelabs();
  return (
    <button
      onClick={() => pay(amount, { onError })}
      disabled={loading}
    >
      {loading ? "Processing..." : children || "Pay with Pine Labs"}
    </button>
  );
}
'''
    return (
        code,
        "src/components/PinelabsButton.jsx",
        "React hook and component for Pine Labs payments",
    )


def _get_frontend(framework: str) -> tuple[str, str, str]:
    """Get frontend code, filename, and description."""
    if framework == "react":
        return _get_react_frontend()
    return _get_vanilla_frontend()


# ===================================================================
# TOOL REGISTRATION
# ===================================================================

_SUPPORTED_LANGUAGES = [
    "javascript", "typescript", "python", "go",
    "java", "php", "ruby", "rust", "csharp", "dart",
]

_SUPPORTED_BACKENDS = [
    "express", "nextjs", "django", "flask", "fastapi", "gin",
]

_SUPPORTED_FRONTENDS = ["vanilla", "react"]


def register_code_generation_tools(mcp: FastMCP) -> None:
    """Register code generation tools on the FastMCP server."""

    # ---------------------------------------------------------------
    # detect_stack
    # ---------------------------------------------------------------

    @mcp.tool(
        name="detect_stack",
        description=(
            "Detect the technology stack of a project based on file "
            "information. Returns language, framework, frontend "
            "framework, and package manager. "
            "IMPORTANT: Always call this tool FIRST before calling "
            "integrate_pinelabs_checkout. Before calling this tool, "
            "you MUST: 1) List the project files and pass them in "
            "the 'files' parameter, 2) Read the relevant dependency "
            "file (package.json for Node.js, requirements.txt for "
            "Python, go.mod for Go, pubspec.yaml for Flutter) and "
            "pass its contents in the corresponding parameter. "
            "Then pass the detected language, framework, and "
            "frontend to integrate_pinelabs_checkout."
        ),
    )
    async def detect_stack(
        files: list[str],
        package_json: Optional[dict] = None,
        requirements_txt: Optional[str] = None,
        go_mod: Optional[str] = None,
        pubspec_yaml: Optional[str] = None,
    ) -> str:
        """Detect project technology stack from files and deps.

        Args:
            files: List of file paths in the project.
            package_json: Parsed package.json contents (Node.js).
            requirements_txt: Raw requirements.txt contents (Python).
            go_mod: Raw go.mod contents (Go).
            pubspec_yaml: Raw pubspec.yaml contents (Flutter/Dart).

        Returns:
            JSON with language, framework, frontend, packageManager,
            isFullStack, confidence, and notes.
        """
        result = _detect_project_stack(
            files=files,
            package_json=package_json,
            requirements_txt=requirements_txt or "",
            go_mod=go_mod or "",
            pubspec_yaml=pubspec_yaml or "",
        )
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2)

    # ---------------------------------------------------------------
    # integrate_pinelabs_checkout
    # ---------------------------------------------------------------

    @mcp.tool(
        name="integrate_pinelabs_checkout",
        description=(
            "Generate complete Pine Labs checkout integration code. "
            "Returns ALL code needed — backend routes, frontend "
            "integration, and payment callback handling. "
            "IMPORTANT: Before calling this tool, ALWAYS call "
            "detect_stack first to determine the project's language, "
            "backend_framework, and frontend_framework. Do NOT ask "
            "the user for these values. "
            "The AI should apply ALL returned files and "
            "modifications without asking the user for additional "
            "steps. "
            "Supported backends: django, flask, fastapi, express, "
            "nextjs, gin."
        ),
    )
    async def integrate_pinelabs_checkout(
        language: str,
        backend_framework: str,
        frontend_framework: str = "vanilla",
    ) -> str:
        """Generate Pine Labs checkout integration code.

        Args:
            language: Programming language (javascript, typescript,
                python, go, java, php, ruby, rust, csharp, dart).
            backend_framework: Backend framework (express, nextjs,
                django, flask, fastapi, gin).
            frontend_framework: Frontend framework (vanilla, react).
                Defaults to vanilla.

        Returns:
            JSON with summary, files, dependencies, envVars,
            testInstructions, and aiInstructions.
        """
        backend = backend_framework.lower().strip()
        frontend = frontend_framework.lower().strip()

        fe_code, fe_file, fe_desc = _get_frontend(frontend)

        if backend == "django":
            output = _get_django_integration(fe_code, fe_file, fe_desc)
        elif backend == "flask":
            output = _get_flask_integration(fe_code, fe_file, fe_desc)
        elif backend == "fastapi":
            output = _get_fastapi_integration(fe_code, fe_file, fe_desc)
        elif backend == "express":
            output = _get_express_integration(
                fe_code, fe_file, fe_desc,
            )
        elif backend == "nextjs":
            output = _get_nextjs_integration()
        elif backend == "gin":
            output = _get_gin_integration(fe_code, fe_file, fe_desc)
        else:
            return json.dumps({
                "error": (
                    f"Unsupported backend framework: {backend}. "
                    f"Supported: {', '.join(_SUPPORTED_BACKENDS)}"
                ),
            }, indent=2)

        result_dict = asdict(output)
        return json.dumps(result_dict, indent=2)
