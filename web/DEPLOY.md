# How to Deploy CovenantAI to Vercel

There are two main ways to deploy this application to Vercel: using the Command Line (fastest) or using GitHub (best for updates).

## Option 1: Command Line (Fastest)

You can deploy directly from your terminal without setting up a GitHub repository first.

1.  **Navigate to the web directory** (if you aren't there already):
    ```bash
    cd web
    ```

2.  **Run the deploy command:**
    ```bash
    npx vercel
    ```

3.  **Follow the prompts:**
    -   **Set up and deploy?** `y`
    -   **Which scope?** Select your account.
    -   **Link to existing project?** `n`
    -   **Project name:** `covenant-ai` (or press Enter for default)
    -   **In which directory is your code located?** `./` (Press Enter)
    -   **Want to modify these settings?** `n` (The defaults for Next.js are correct)

4.  **Wait for deployment:**
    Vercel will build your project and give you a `Production: https://...` URL.

## Option 2: GitHub Integration (Recommended for Production)

This method automatically redeploys your site whenever you push changes to GitHub.

1.  **Push your code to GitHub:**
    -   Create a new repository on GitHub.
    -   Push this `covenant_systems` folder to it.

2.  **Go to Vercel Dashboard:**
    -   Log in to [vercel.com](https://vercel.com).
    -   Click **"Add New..."** -> **"Project"**.
    -   Import your GitHub repository.

3.  **Configure Project:**
    -   **Framework Preset:** Next.js (should be auto-detected).
    -   **Root Directory:** Click "Edit" and select the `web` folder. **(Crucial Step)**
    -   Click **Deploy**.

## Troubleshooting

-   **Build Fails?** Check the logs on Vercel. Ensure `npm run build` works locally.
-   **Styles Missing?** Ensure Tailwind is configured correctly (it should be out of the box).
