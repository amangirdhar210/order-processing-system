from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.serverful.utils.errors import ApplicationError


async def application_error_handler(request: Request, exc: ApplicationError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()

    invalid_fields = []
    for error in errors:
        field = error["loc"][-1]
        if field not in invalid_fields:
            invalid_fields.append(field)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error_code": 4220,
            "message": "Invalid input",
            "details": (
                f"Invalid field: {invalid_fields[0]}"
                if len(invalid_fields) == 1
                else f"Invalid fields: {', '.join(invalid_fields)}"
            ),
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error_code": 9001, "message": "Internal server error"},
    )
