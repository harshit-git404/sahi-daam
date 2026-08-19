# Data Schemas

## wholesale_prices.json
```json
{
  "<commodity_name>": {
    "<location>": {
      "<date_YYYY-MM-DD>": <price_as_number>
    }
  }
}
```

## quickcommerce_snapshot.json
```json
{
  "<commodity_name>": {
    "<source_name>": {
      "<date_YYYY-MM-DD>": {
        "price": <price_as_number>,
        "unit": "<unit_string>"
      }
    }
  }
}
```
