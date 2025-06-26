# Strava Integration Setup Guide

This guide will walk you through connecting your Running Heatmap to your Strava account. This will allow you to automatically sync your latest runs.

## Step 1: Create a Strava API Application

Before the application can access your data, you need to give it permission by creating a personal Strava API application.

1.  **Log in to Strava**: Go to [https://www.strava.com/settings/api](https://www.strava.com/settings/api) and log in with your Strava account.

2.  **Create a New Application**: Fill out the form as follows:
    *   **Application Name**: `Running Heatmap` (or anything you like)
    *   **Website**: `https://localhost`
    *   **Application Description**: `Personal heatmap of my runs`
    *   **Authorization Callback Domain**: `localhost`

3.  **Save the Application**: Agree to the terms and click "Create".

4.  **Get Your Credentials**: You will now see your new application's details. Keep this page open. You will need the **Client ID** and **Client Secret** for the next step.

## Step 2: Configure the Application

Now you need to provide your Strava API credentials to the Running Heatmap application.

1.  **Navigate to the `server` directory** in your project.

2.  **Create `config.ini`**: You will see a file named `config.ini.template`. Make a copy of this file and rename it to `config.ini`.

3.  **Edit `config.ini`**: Open the new `config.ini` file in a text editor. It will look like this:

    ```ini
    [strava]
    client_id = YOUR_CLIENT_ID
    client_secret = YOUR_CLIENT_SECRET
    ```

4.  **Add Your Credentials**: Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with the values from your Strava API application page.

    **Important**: The `config.ini` file is included in `.gitignore`, so your secret credentials will **not** be committed to your repository.

## Step 3: Authorize the Application

The final step is to grant the application permission to access your Strava data.

1.  **Navigate to the `server` directory** in your terminal.

2.  **Run the authorization script**:

    ```bash
    python strava_client.py
    ```

3.  **Authorize in Browser**: Your web browser will automatically open a Strava authorization page. Click **Authorize**.

4.  **Confirmation**: After you authorize, you will be redirected to a `localhost` page with a success message. You can close this browser tab.

5.  **Check Your Terminal**: The script will confirm that it has successfully received the authorization tokens.

That's it! Your application is now securely connected to your Strava account. A new file, `strava_tokens.json`, has been created in the `server` directory to store your authentication tokens.
