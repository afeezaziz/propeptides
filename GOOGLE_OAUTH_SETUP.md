# Google OAuth2 Setup Instructions

## Prerequisites
- Google Cloud Console account
- Domain: https://propeptides.angpao.my

## Step 1: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Google+ API**
   - **People API**
   - **OAuth 2.0 API**

## Step 2: Create OAuth2 Credentials

1. Navigate to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Select **Web application** as the application type
4. Configure the following:

### Authorized JavaScript origins:
```
https://propeptides.angpao.my
```

### Authorized redirect URIs:
```
https://propeptides.angpao.my/authorize
```

## Step 3: Update Environment Variables

Copy the Client ID and Client Secret from Google Cloud Console and update your `.env` file:

```bash
GOOGLE_CLIENT_ID=your_actual_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
SECRET_KEY=generate_a_secure_random_secret_key
```

## Step 4: Generate Secure Secret Key

Run this Python command to generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 5: Production Settings

The application is configured for production:
- `DEBUG=False`
- `OAUTHLIB_INSECURE_TRANSPORT=0` (requires HTTPS)
- Uses the production domain `https://propeptides.angpao.my`

## Step 6: Test the Integration

1. Restart your Flask application
2. Visit https://propeptides.angpao.my
3. Click the "Login" button
4. You should be redirected to Google's OAuth2 consent screen
5. After granting permission, you'll be redirected back to the dashboard

## Troubleshooting

### Common Issues:

1. **Redirect URI Mismatch**: Ensure the redirect URI in Google Cloud Console exactly matches `https://propeptides.angpao.my/authorize`

2. **HTTPS Required**: OAuth2 requires HTTPS in production. Make sure your domain has proper SSL/TLS certificates

3. **Domain Verification**: You may need to verify domain ownership in Google Search Console

4. **CORS Issues**: If you encounter CORS errors, ensure the domain is properly configured in Google Cloud Console

### Environment Variables Checklist:

- [ ] `GOOGLE_CLIENT_ID` is set correctly
- [ ] `GOOGLE_CLIENT_SECRET` is set correctly
- [ ] `SECRET_KEY` is a secure random value
- [ ] `DEBUG=False` for production
- [ ] `OAUTHLIB_INSECURE_TRANSPORT=0` for production

### Google Cloud Console Checklist:

- [ ] Project is created and selected
- [ ] Required APIs are enabled
- [ ] OAuth2 consent screen is configured
- [ ] Web application credentials are created
- [ ] Authorized JavaScript origins include `https://propeptides.angpao.my`
- [ ] Authorized redirect URIs include `https://propeptides.angpao.my/authorize`

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables in production
- Regularly rotate your OAuth2 secrets
- Monitor Google Cloud Console for unusual activity
- Implement proper session timeout policies

## Support

If you encounter any issues with the OAuth2 setup, check the Google Cloud Console documentation or contact your system administrator.