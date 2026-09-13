# Fipe -- a FIPE and car-market agent, built FROM the plow-hermes-agent base.
#
# No boot, no gateway config, no model wiring here: those are the base's, and
# arrive as a digest bump. This repo adds one thing -- the persona and skills
# of one assistant -- plus the Agent Index reporter and the process timezone.
#
# The tag is an immutable base-<sha> naming one commit of
# plow-pbc/plow-hermes-agent, resolved to a digest, so a moving tag can never
# substitute different bytes under a running agent.
FROM public.ecr.aws/e1h7x4a2/plow-cloud-agents:base-ef4b30e00e74b4f2c47832acecfacb5eba717468@sha256:693ac5520ec0a2cabe8fc9de6a0c4827b79a7a0556228345aaf63664a001d7b4

# Identity: only what is specific to this agent. plow-init composes the home's
# SOUL.md on every boot as the base persona followed by this file. Never COPY
# anything to /var/lib/hermes/SOUL.md -- the boot overwrites it.
COPY --chmod=0644 persona.md /opt/hermes/plow-seed/persona.md
COPY LICENSE NOTICE /usr/share/doc/fipe/

# Shipped at /opt/hermes/skills, outside every home, so the base runtime's
# reconcile seeds them into a home that lacks them and still reaches a home
# whose owner has not customised them. A skill the agent deleted stays
# deleted; one it edited stays edited.
COPY skills/ /opt/hermes/skills/

# Normalize whatever modes the checkout carried, preserving the executable
# bit: SKILL.md files invoke scripts, so a blanket 0644 would break them. The
# skills root itself is the base's; -mindepth 1 keeps its mode intact.
RUN find /opt/hermes/skills -mindepth 1 -type d -exec chmod 0755 {} + \
 && find /opt/hermes/skills -mindepth 1 -type f ! -perm -u+x -exec chmod 0644 {} + \
 && find /opt/hermes/skills -mindepth 1 -type f -perm -u+x -exec chmod 0755 {} +

# The Agent Index usage reporter, fetched at build from the commit
# vendor/client.pin names and checked against the hash beside it. Root-owned
# under /opt/plow: the copy in the agent's home belongs to uid 10000 in a
# running container, so scheduling that one would run whatever a turn last
# wrote there.
COPY vendor/client.pin /opt/plow/agent-index-client.pin
RUN set -eu; \
    sha="$(sed -n 's/^sha=//p' /opt/plow/agent-index-client.pin)"; \
    want="$(sed -n 's/^sha256=//p' /opt/plow/agent-index-client.pin)"; \
    path="$(sed -n 's/^path=//p' /opt/plow/agent-index-client.pin)"; \
    curl -fsS --max-time 60 -o /opt/plow/agent-index-client.py \
      "https://raw.githubusercontent.com/plow-pbc/agent-index-client/${sha}/${path}"; \
    got="$(sha256sum /opt/plow/agent-index-client.py | cut -d' ' -f1)"; \
    [ "$got" = "$want" ] || { echo "agent-index client is $got, pin says $want" >&2; exit 1; }; \
    chmod 0644 /opt/plow/agent-index-client.py

# The reporter's supervised service beside the gateway, and this agent's
# oneshots. COPYed over the base's tree -- it adds services, it removes none.
COPY image/s6-overlay/ /etc/s6-overlay/

# The process timezone, resolved from this agent's config before any service
# starts. The base sets none; every cron schedule this agent registers fires
# in whatever this leaves behind.
COPY --chmod=0755 image/cont-init.d/10-fipe-timezone /etc/cont-init.d/10-fipe-timezone

# The instance directory the skills read and onboarding writes: followed
# teams, the news cache, config. Empty until first boot; owned by the agent's
# uid.
RUN install -d -o 10000 -g 10000 -m 0700 /var/lib/hermes/fipe