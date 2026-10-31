# Civis consultations digest

Every morning at about 9:35 AM IST, GitHub runs `civis_digest.py`. It fetches the public consultations currently open on [Civis](https://www.civis.vote/consultations/list) and posts the list to Slack.

The message lists consultations closing within 48 hours first. Each item shows a clickable title, the ministry and the deadline in IST, and anything added in the last 24 hours is tagged :new:. If Civis can't be reached, a "digest skipped today" message is posted instead, so a missing digest never goes unnoticed.

## One-time setup

### 1. Get a Slack webhook URL (choose one)

**Option A: Workflow Builder.** This uses Slack itself, with no app to install. It needs a paid Slack plan.

1. In Slack, open **Tools → Workflows → New workflow → Build workflow**.
2. Under *Start the workflow*, choose **From a webhook**.
3. Add a variable named exactly `digest`, of type *Text*.
4. Add the step **Messages → Send a message to a person**, choose yourself, and insert the `digest` variable as the message.
5. Publish the workflow and copy the webhook URL it shows (it starts with `https://hooks.slack.com/triggers/...`).

**Option B: Incoming webhook.** This works on any plan, but it creates a small Slack app, and some workspaces need admin approval.

1. Go to <https://api.slack.com/apps>, then choose **Create New App → From scratch**, and pick your workspace.
2. Open **Incoming Webhooks**, switch it **On**, then choose **Add New Webhook to Workspace**.
3. Pick where the messages should go: yourself, or a channel.
4. Copy the URL (it starts with `https://hooks.slack.com/services/...`).

### 2. Put the code on GitHub

1. Create a **new repository** on GitHub, e.g. `civis-digest`. It can be **private**.
2. Upload `civis_digest.py`, `README.md` and the workflow file. The workflow file must sit at exactly this path: `.github/workflows/civis-digest.yml`.

### 3. Add the webhook as a secret

In the repo, open **Settings → Secrets and variables → Actions → New repository secret**.
- Name: `SLACK_WEBHOOK_URL`
- Value: the URL from step 1

The URL stays hidden from anyone who views the code.

### 4. Test it

Go to the repo's **Actions** tab, choose **Civis consultations digest**, then click **Run workflow**. The message should arrive in Slack within a minute. After that it runs by itself every morning.

## Notes

- **Changing the time:** edit the `cron` line in the workflow file. It's in UTC, so 9:35 AM IST is `5 4 * * *`. GitHub sometimes runs scheduled jobs several minutes late.
- **Pausing it:** go to the **Actions** tab, open the workflow's **⋯** menu, and choose **Disable workflow**.
- **Keeping it running:** GitHub pauses scheduled workflows in repos that have had no activity for 60 days. It emails a warning first, and re-enabling it takes one click.
- **Previewing the message:** with Python installed, run `DRY_RUN=1 python civis_digest.py` to print the message without posting it.
- **About the data:** Civis's API is public but not officially documented as a public API, and the consultation summaries are Civis's own curated work. The script makes one request per day.
