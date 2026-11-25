from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.github_actions import iter_jobs


@rule(
    id="GA008",
    title="Reusable workflow inherits all secrets from external repository",
    severity="high",
    cwe=200,
)
def check(ctx: Context) -> Iterable[Finding]:
    """A job passes `secrets: inherit` to a reusable workflow in another repository.

    Why it matters: `secrets: inherit` exposes every repository and organization
    secret configured for the caller workflow to the called workflow. When `uses:`
    points outside the current repository, that external repository's owners
    control what happens to all of your secrets (see GitHub's security hardening
    guide for reusable workflows).

    Fix: pass only the specific secrets the external workflow actually needs:

        jobs:
          deploy:
            uses: octo-org/shared/.github/workflows/deploy.yml@<40-character-sha>
            secrets:
              DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
    """
    if ctx.workflow is None:
        return
    for _job_id, job in iter_jobs(ctx.workflow):
        uses = job.get("uses")
        secrets = job.get("secrets")
        if not isinstance(uses, str) or uses.startswith("./"):
            continue
        if isinstance(secrets, str) and secrets == "inherit":
            yield ctx.finding(
                job.key_lines["secrets"],
                f"`secrets: inherit` shares all caller secrets with external workflow `{uses}`.",
                "Pass only explicit secrets under `secrets:`, e.g. `TOKEN: ${{ secrets.TOKEN }}`.",
            )
