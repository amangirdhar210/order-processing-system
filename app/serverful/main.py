from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.serverful.lifespan import lifespan
from app.serverful.controllers.auth_controllers import auth_router
from app.serverful.controllers.admin_auth_controllers import admin_auth_router
from app.serverful.controllers.customer_order_controllers import order_router
from app.serverful.controllers.admin_order_controllers import staff_router
from app.serverful.utils.exception_handlers import (
    application_error_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.serverful.utils.errors import ApplicationError


app = FastAPI(
    title="Order Processing System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(admin_auth_router, tags=["Admin - User Management"])
app.include_router(order_router, tags=["Customer Orders"])
app.include_router(staff_router, prefix="/staff", tags=["Staff Orders"])