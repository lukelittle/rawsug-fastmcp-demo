# Generate config.js from template with API Gateway URL
resource "local_file" "config_js" {
  content = templatefile("${path.module}/../web/config.js.tmpl", {
    api_base_url = aws_apigatewayv2_stage.default.invoke_url
  })
  filename = "${path.module}/../web/config.js"
}

# Upload index.html
resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.website.id
  key          = "index.html"
  source       = "${path.module}/../web/index.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../web/index.html")
}

# Upload app.js
resource "aws_s3_object" "app_js" {
  bucket       = aws_s3_bucket.website.id
  key          = "app.js"
  source       = "${path.module}/../web/app.js"
  content_type = "application/javascript"
  etag         = filemd5("${path.module}/../web/app.js")
}

# Upload styles.css
resource "aws_s3_object" "styles_css" {
  bucket       = aws_s3_bucket.website.id
  key          = "styles.css"
  source       = "${path.module}/../web/styles.css"
  content_type = "text/css"
  etag         = filemd5("${path.module}/../web/styles.css")
}

# Upload generated config.js
resource "aws_s3_object" "config_js" {
  bucket       = aws_s3_bucket.website.id
  key          = "config.js"
  source       = local_file.config_js.filename
  content_type = "application/javascript"
  etag         = local_file.config_js.content_md5

  depends_on = [local_file.config_js]
}
