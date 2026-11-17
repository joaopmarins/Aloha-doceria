#!/usr/bin/env bash
# Checagem estática dos requisitos do design (docs/design.md). Uso: bash tests/check.sh
cd "$(dirname "$0")/.." || exit 1
H=index.html C=style.css falhas=0
ok()  { if eval "$2" >/dev/null 2>&1; then echo "OK    $1"; else echo "FALHA $1"; falhas=$((falhas+1)); fi; }
tem() { grep -qF -- "$2" "$1"; }

ok "lang pt-BR"                 'tem $H "lang=\"pt-BR\""'
ok "viewport-fit=cover"         'tem $H "viewport-fit=cover"'
ok "link WhatsApp exato (1x)"   '[ "$(grep -oF "https://wa.me/5519996492363?text=Ol%C3%A1!%20Vim%20pelo%20site" $H | wc -l)" = 1 ]'
ok "link do mapa"               'tem $H "google.com/maps/search/?api=1&amp;query=Av.%20Em%C3%ADlio%20B%C3%B4sco"'
ok "mailto do crédito"          'tem $H "mailto:joaopfmarins@gmail.com"'
ok "texto do crédito"           'tem $H "Feito por João Marins"'
ok "aria-label WhatsApp"        'tem $H "aria-label=\"Conversar no WhatsApp\""'
ok "alt da logo"                'tr "\n" " " < $H | grep -qE "<img[^>]+src=\"assets/logo[^>]+alt=\"[^\"]+\""'
ok "og:image absoluto"          'tem $H "property=\"og:image\" content=\"https://"'
ok "og.png 1200x630"            'file og.png | grep -q "1200 x 630"'
ok "og.png < 200KB"             '[ $(stat -c%s og.png) -lt 204800 ]'
ok "≥4 PLACEHOLDER"             '[ $(grep -c "<!-- PLACEHOLDER -->" $H) -ge 4 ]'
ok "sem Lorem/TODO/R\$/entrega" '! grep -qiE "lorem|todo|R\\$|entrega" $H'
ok "safe-area no CSS"           'tem $C "env(safe-area-inset-bottom)"'
ok "prefers-reduced-motion"     'tem $C "prefers-reduced-motion"'
for v in rosa rosa-claro azul azul-escuro amarelo verde laranja; do
  ok "variável --$v"            "grep -qE -- '--$v:' $C"
done
ok "footer padding-bottom ≥88px" 'grep -qE "\.rodape *\{[^}]*padding-bottom: *(calc\\()?(8[89]|9[0-9]|1[0-9][0-9])px" <(tr -d "\n" < $C)'

ok "deploy só publica o site (allowlist)" 'grep -qx "/\*" .vercelignore && grep -qx "!index.html" .vercelignore'
ok "foco visível no rodapé escuro" 'tr -d "\n" < $C | grep -qE "\.rodape :focus-visible[^{]*\{[^}]*outline-color: *var\(--amarelo\)"'
ok "rodapé soma safe-area" 'tem $C "padding-bottom: calc(96px + env(safe-area-inset-bottom))"'
ok "sem salgados (não confirmado)" '! grep -qi "salgados" $H'

echo "---"; [ $falhas -eq 0 ] && echo "TUDO OK" || { echo "$falhas falha(s)"; exit 1; }
