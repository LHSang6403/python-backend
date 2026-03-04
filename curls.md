# User API Curls

## Create user

```bash
curl -s -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "secret123", "full_name": "John Doe"}' | python -m json.tool
```

## List users

```bash
curl -s http://localhost:8000/api/v1/users | python -m json.tool
```

## List users with pagination

```bash
curl -s "http://localhost:8000/api/v1/users?skip=0&limit=10" | python -m json.tool
```

## Get user by ID

```bash
curl -s http://localhost:8000/api/v1/users/USER_ID | python -m json.tool
```

## Update user

```bash
curl -s -X PATCH http://localhost:8000/api/v1/users/USER_ID \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Updated", "is_active": false}' | python -m json.tool
```

## Delete user

```bash
curl -s -X DELETE -w "%{http_code}\n" http://localhost:8000/api/v1/users/USER_ID
```

# Product API Curls

## Create product (requires auth)

```bash
curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -d '{"name": "Laptop", "description": "A powerful laptop", "price": 999.99, "quantity": 10}' | python -m json.tool
```

## List products (requires auth)

```bash
curl -s http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer ACCESS_TOKEN" | python -m json.tool
```

## List products with pagination (requires auth)

```bash
curl -s "http://localhost:8000/api/v1/products?skip=0&limit=10" \
  -H "Authorization: Bearer ACCESS_TOKEN" | python -m json.tool
```

## Get product by ID (requires auth)

```bash
curl -s http://localhost:8000/api/v1/products/PRODUCT_ID \
  -H "Authorization: Bearer ACCESS_TOKEN" | python -m json.tool
```

## Update product (requires auth)

```bash
curl -s -X PATCH http://localhost:8000/api/v1/products/PRODUCT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -d '{"name": "Laptop Pro", "price": 1299.99, "is_active": false}' | python -m json.tool
```

## Delete product (requires auth)

```bash
curl -s -X DELETE -w "%{http_code}\n" http://localhost:8000/api/v1/products/PRODUCT_ID \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

# Order API Curls

## Create order (requires auth)

```bash
curl -s -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -d '{"items": [{"product_id": "PRODUCT_ID", "quantity": 2}]}' | python -m json.tool
```

## Create order with multiple items (requires auth)

```bash
curl -s -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -d '{"items": [{"product_id": "PRODUCT_ID_1", "quantity": 2}, {"product_id": "PRODUCT_ID_2", "quantity": 1}]}' | python -m json.tool
```

## List orders (requires auth)

```bash
curl -s http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer ACCESS_TOKEN" | python -m json.tool
```

## List orders with pagination (requires auth)

```bash
curl -s "http://localhost:8000/api/v1/orders?skip=0&limit=10" \
  -H "Authorization: Bearer ACCESS_TOKEN" | python -m json.tool
```

## Get order by ID (requires auth)

```bash
curl -s http://localhost:8000/api/v1/orders/ORDER_ID \
  -H "Authorization: Bearer ACCESS_TOKEN" | python -m json.tool
```

# PASETO Auth API Curls

## Login (PASETO)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/paseto/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "secret123"}' | python -m json.tool
```

## Refresh (PASETO)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/paseto/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "PASETO_REFRESH_TOKEN"}' | python -m json.tool
```

## Logout (PASETO)

```bash
curl -s -X POST -w "%{http_code}\n" http://localhost:8000/api/v1/auth/paseto/logout \
  -H "Authorization: Bearer PASETO_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "PASETO_REFRESH_TOKEN"}'
```
