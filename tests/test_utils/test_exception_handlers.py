import pytest
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from unittest.mock import Mock
from app.serverful.utils.exception_handlers import (
    application_error_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.serverful.utils.errors import ApplicationError, ErrorCode


class TestApplicationErrorHandler:
    @pytest.mark.asyncio
    async def test_application_error_handler_with_details(self):
        request = Mock(spec=Request)
        error = ApplicationError(
            ErrorCode.USER_NOT_FOUND,
            details="User ID user123 not found"
        )
        
        response = await application_error_handler(request, error)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        content = response.body.decode()
        assert "USER_NOT_FOUND" in content or "2001" in content
        assert "User not found" in content

    @pytest.mark.asyncio
    async def test_application_error_handler_unauthorized(self):
        request = Mock(spec=Request)
        error = ApplicationError(ErrorCode.UNAUTHORIZED)
        
        response = await application_error_handler(request, error)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestValidationExceptionHandler:
    @pytest.mark.asyncio
    async def test_validation_exception_single_field(self):
        request = Mock(spec=Request)
        
        class TestModel(BaseModel):
            email: str
        
        try:
            TestModel(email=123)
        except ValidationError as ve:
            exc = RequestValidationError(errors=ve.errors())
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        content = response.body.decode()
        assert "Invalid field" in content
        assert "4220" in content

    @pytest.mark.asyncio
    async def test_validation_exception_multiple_fields(self):
        request = Mock(spec=Request)
        
        class TestModel(BaseModel):
            email: str
            age: int
        
        try:
            TestModel(email=123, age="not_an_int")
        except ValidationError as ve:
            exc = RequestValidationError(errors=ve.errors())
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        content = response.body.decode()
        assert "Invalid fields" in content


class TestGeneralExceptionHandler:
    @pytest.mark.asyncio
    async def test_general_exception_handler(self):
        request = Mock(spec=Request)
        error = Exception("Unexpected error occurred")
        
        response = await general_exception_handler(request, error)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        content = response.body.decode()
        assert "9001" in content
        assert "Internal server error" in content
