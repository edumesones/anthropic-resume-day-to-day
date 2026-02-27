"""
Scraper principal para obtener actualizaciones de Anthropic.
Genera resumen diario en TRES CARPETAS separadas.
"""
import os
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from github import Github


class AnthropicScraper:
    """Scraper para fuentes de Anthropic."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.github = Github(github_token) if github_token else None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_research(self) -> List[Dict]:
        """Obtiene papers de research de Anthropic - solo los más recientes."""
        from datetime import datetime
        
        url = "https://www.anthropic.com/research"
        papers = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # La página de Anthropic tiene un grid de publicaciones
            # Cada item es un enlace a /research/[slug]
            items = soup.select('a[href^="/research/"]')
            print(f"  Encontrados {len(items)} posibles papers")
            
            for item in items:
                try:
                    href = item.get('href', '')
                    if not href or href == '/research/':
                        continue
                    
                    link = f"https://www.anthropic.com{href}"
                    
                    # Buscar el contenedor del paper (article o div padre)
                    container = item.find_parent(['article', 'div[data-testid]']) or item
                    
                    # Título - buscar específicamente en heading elements dentro de la tarjeta
                    title_elem = container.select_one('h3, h2, h4')
                    title = ""
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # Si no hay heading, intentar extraer del link
                    if not title:
                        text_lines = [line.strip() for line in item.get_text().split('\n') if line.strip()]
                        if len(text_lines) >= 2:
                            title = text_lines[-1]  # Última línea suele ser el título
                        elif text_lines:
                            title = text_lines[0]
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Filtrar navegación/cookies/páginas no-paper
                    skip_keywords = ['cookie', 'privacy', 'gdpr', 'terms', 'team', 'careers', 'jobs', 'research overview']
                    if any(x in title.lower() for x in skip_keywords):
                        continue
                    
                    # Descripción
                    desc_elem = container.select_one('p[class*="description"], p[class*="summary"], article p')
                    description = ""
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                    
                    # Fecha - buscar específicamente
                    date_str = ""
                    date_elem = container.select_one('time')
                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    else:
                        full_text = container.get_text()
                        import re
                        # Buscar patrón de fecha
                        date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', full_text, re.IGNORECASE)
                        if date_match:
                            date_str = date_match.group()
                    
                    papers.append({
                        'title': title,
                        'description': description[:400] + "..." if len(description) > 400 else description,
                        'url': link,
                        'date': date_str,
                        'source': 'anthropic.com/research'
                    })
                    
                except Exception as e:
                    print(f"Error procesando paper: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scrapeando research: {e}")
            papers.append({
                'error': True,
                'message': f'No se pudo obtener research: {str(e)}',
                'suggestion': 'Visitar https://www.anthropic.com/research manualmente'
            })
            return papers
        
        # Ordenar por fecha (más recientes primero) y tomar solo los 5 últimos
        if papers and not papers[0].get('error'):
            papers = self._sort_by_date(papers)
            papers = papers[:5]  # Solo los 5 más recientes
            print(f"  Papers más recientes: {len(papers)}")
        
        return papers
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parsea fecha string a datetime para ordenar."""
        from dateutil import parser as date_parser
        try:
            return date_parser.parse(date_str)
        except:
            # Si no se puede parsear, devolver fecha muy antigua
            return datetime.min
    
    def _sort_by_date(self, items: List[Dict]) -> List[Dict]:
        """Ordena items por fecha (más recientes primero)."""
        return sorted(items, key=lambda x: self._parse_date(x.get('date', '')), reverse=True)
    
    def scrape_docs(self) -> List[Dict]:
        """Docs se obtienen via GitHub (claude-code repo). Esta función ya no se usa."""
        return []
    
    def get_github_updates(self, org_name: str = "anthropics", days_back: int = 2) -> List[Dict]:
        """Obtiene actualizaciones de repos de Anthropic en GitHub."""
        if not self.github:
            return [{
                'error': True,
                'message': 'GitHub token no configurado'
            }]
        
        from datetime import timezone
        
        updates = []
        # Crear fecha aware (con timezone) para comparar correctamente
        yesterday = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        try:
            org = self.github.get_organization(org_name)
            repos = org.get_repos(type='public', sort='updated')
            
            print(f"  Revisando {repos.totalCount} repos de {org_name}...")
            
            for repo in repos[:30]:  # Aumentar a 30 repos
                try:
                    # Convertir updated_at a aware si es naive
                    repo_updated = repo.updated_at
                    if repo_updated.tzinfo is None:
                        repo_updated = repo_updated.replace(tzinfo=timezone.utc)
                    
                    if repo_updated < yesterday:
                        continue
                    
                    print(f"    📁 {repo.name} - revisando actividad...")
                    
                    # Obtener commits recientes
                    recent_commits = []
                    try:
                        commits = repo.get_commits(since=yesterday)
                        for commit in commits[:5]:  # Top 5 commits
                            commit_date = commit.commit.author.date
                            if commit_date.tzinfo is None:
                                commit_date = commit_date.replace(tzinfo=timezone.utc)
                            
                            recent_commits.append({
                                'message': commit.commit.message.split('\n')[0][:100],
                                'url': commit.html_url,
                                'author': commit.commit.author.name,
                                'date': commit_date.isoformat()
                            })
                    except Exception as e:
                        print(f"      Error obteniendo commits: {e}")
                    
                    # Obtener releases recientes
                    recent_releases = []
                    try:
                        releases = repo.get_releases()
                        for release in releases[:2]:  # Top 2 releases
                            release_date = release.created_at
                            if release_date and release_date.tzinfo is None:
                                release_date = release_date.replace(tzinfo=timezone.utc)
                            
                            if release_date and release_date > yesterday:
                                recent_releases.append({
                                    'tag': release.tag_name,
                                    'name': release.title,
                                    'url': release.html_url,
                                    'body': (release.body[:500] + "...") if release.body and len(release.body) > 500 else (release.body or "")
                                })
                    except Exception as e:
                        print(f"      Error obteniendo releases: {e}")
                    
                    # Si hay actividad, agregar al reporte
                    if recent_commits or recent_releases:
                        update_info = {
                            'name': repo.name,
                            'url': repo.html_url,
                            'description': repo.description or "No description",
                            'stars': repo.stargazers_count,
                            'language': repo.language or "Unknown",
                            'updated_at': repo_updated.isoformat(),
                            'commits': recent_commits,
                            'releases': recent_releases
                        }
                        
                        updates.append(update_info)
                        print(f"      ✅ {len(recent_commits)} commits, {len(recent_releases)} releases")
                        
                except Exception as e:
                    print(f"    ⚠️ Error procesando repo {repo.name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error accediendo a GitHub: {e}")
            updates.append({
                'error': True,
                'message': f'Error accediendo a GitHub: {str(e)}'
            })
        
        print(f"\n  Total repos con actividad: {len(updates)}")
        return updates
    
    def calculate_utility(self, repo_update: Dict) -> tuple:
        """Calcula utilidad del cambio (score 1-5, descripción)."""
        score = 3
        reasons = []
        
        stars = repo_update.get('stars', 0)
        if stars > 10000:
            score += 1
            reasons.append("Repo muy popular")
        elif stars < 100:
            score -= 1
            reasons.append("Repo menos conocido")
        
        release = repo_update.get('release')
        commits = repo_update.get('commits', [])
        
        if release:
            score += 1
            reasons.append("Nueva release disponible")
            
            tag = release.get('tag', '')
            if tag.startswith('v') and ('.0.' in tag or tag.endswith('.0')):
                score += 1
                reasons.append("Posible versión mayor")
        
        if commits:
            important_keywords = ['feat', 'feature', 'add', 'implement', 'breaking', 'major']
            for commit in commits[:2]:
                msg = commit.get('message', '').lower()
                if any(kw in msg for kw in important_keywords):
                    score += 1
                    reasons.append("Nuevas funcionalidades")
                    break
        
        lang = repo_update.get('language', '').lower()
        if lang in ['python', 'javascript', 'typescript']:
            reasons.append("Lenguaje popular")
        
        score = max(1, min(5, score))
        
        return score, reasons


def generate_research_markdown(date_str: str, papers: List[Dict]) -> str:
    """Genera markdown solo para Research."""
    lines = [
        f"# Research - {date_str}",
        "",
        f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
    ]
    
    if papers and not papers[0].get('error'):
        lines.append(f"## Papers encontrados: {len(papers)}")
        lines.append("")
        
        for paper in papers[:10]:
            lines.extend([
                f"### [{paper['title']}]({paper['url']})",
                "",
            ])
            if paper.get('date'):
                lines.append(f"**Fecha**: {paper['date']}")
                lines.append("")
            if paper.get('description'):
                lines.append(paper['description'])
                lines.append("")
            lines.append(f"**Link**: [{paper['url']}]({paper['url']})")
            lines.append("")
            lines.append("---")
            lines.append("")
    elif papers and papers[0].get('error'):
        lines.append(f"⚠️ **Error**: {papers[0].get('message', 'No disponible')}")
        lines.append("")
    else:
        lines.append("No se encontraron nuevos papers de research.")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "*Fuente*: [anthropic.com/research](https://www.anthropic.com/research)",
        "",
        "*Generado automáticamente*",
    ])
    
    return '\n'.join(lines)


def generate_docs_markdown(date_str: str, docs: List[Dict]) -> str:
    """Genera markdown solo para Docs (Changelog de Claude Code)."""
    lines = [
        f"# Changelog Claude Code - {date_str}",
        "",
        f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
    ]
    
    # Filtrar solo entradas de versión (no metadatos como commits recientes)
    version_entries = [d for d in docs if d.get('version')]
    commit_info = next((d for d in docs if d.get('recent_commits')), None)
    
    if version_entries:
        lines.append(f"## Versiones recientes: {len(version_entries)}")
        lines.append("")
        
        for entry in version_entries:
            version = entry['version']
            changes = entry.get('changes', [])
            
            lines.extend([
                f"### v{version}",
                "",
                "**Cambios:**",
                "",
            ])
            
            for change in changes[:10]:  # Max 10 cambios por versión
                lines.append(f"- {change}")
            
            lines.append("")
            lines.append(f"[Ver en GitHub]({entry['url']}#v{version.replace('.', '')})")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Añadir info de commits recientes si existe
        if commit_info and commit_info.get('recent_commits'):
            lines.append("### Commits recientes al CHANGELOG")
            lines.append("")
            for commit in commit_info['recent_commits'][:5]:
                lines.append(f"- `{commit['sha']}` {commit['message']} ({commit['date'][:10]})")
            lines.append("")
            
    elif docs and docs[0].get('info'):
        lines.append(f"ℹ️ {docs[0].get('message', 'Sin novedades')}")
        lines.append("")
    elif docs and docs[0].get('error'):
        lines.append(f"⚠️ **Error**: {docs[0].get('message', 'No disponible')}")
        lines.append("")
    else:
        lines.append("No se encontraron actualizaciones de documentación.")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "*Fuente*: [github.com/anthropics/claude-code/CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)",
        "",
        "*Generado automáticamente*",
    ])
    
    return '\n'.join(lines)


def generate_github_markdown(date_str: str, repos: List[Dict]) -> str:
    """Genera markdown solo para GitHub."""
    lines = [
        f"# GitHub - {date_str}",
        "",
        f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
    ]
    
    if repos and not repos[0].get('error'):
        lines.append(f"## Repositorios con actividad reciente: {len(repos)}")
        lines.append("")
        
        scraper = AnthropicScraper()
        
        for repo in repos[:15]:
            lines.extend([
                f"### `{repo['name']}`",
                "",
            ])
            
            if repo.get('description'):
                lines.append(f"*{repo['description']}*")
                lines.append("")
            
            # Info del repo
            lines.append(f"⭐ {repo.get('stars', 0)} stars | 📝 {repo.get('language', 'Unknown')}")
            lines.append("")
            
            if repo.get('commits'):
                lines.append(f"**Commits ({len(repo['commits'])}):**")
                lines.append("")
                for commit in repo['commits'][:5]:
                    msg = commit.get('message', '')[:80]
                    if len(commit.get('message', '')) > 80:
                        msg += "..."
                    author = commit.get('author', 'Unknown')
                    lines.append(f"- `{author}`: [{msg}]({commit['url']})")
                lines.append("")
            
            # Releases (puede ser múltiple)
            releases = repo.get('releases', [])
            if releases:
                lines.append(f"**Releases ({len(releases)}):**")
                lines.append("")
                for release in releases[:2]:
                    lines.append(f"- [{release['tag']}]({release['url']}) - {release['name']}")
                    if release.get('body'):
                        body = release['body'][:150].replace('\n', ' ')
                        lines.append(f"  > {body}...")
                lines.append("")
            elif repo.get('release'):  # Backward compatibility
                release = repo['release']
                lines.append(f"**Release**: [{release['tag']}]({release['url']})")
                lines.append("")
            
            score, reasons = scraper.calculate_utility(repo)
            stars = "⭐" * score
            lines.append(f"**Importancia**: {stars} ({score}/5)")
            if reasons:
                lines.append(f"*Por qué: {', '.join(reasons)}*")
            lines.append("")
            
            lines.append(f"[Ver en GitHub →]({repo['url']})")
            lines.append("")
            lines.append("---")
            lines.append("")
    elif repos and repos[0].get('error'):
        lines.append(f"⚠️ **Error**: {repos[0].get('message', 'No disponible')}")
        lines.append("")
    else:
        lines.append("No se encontró actividad reciente en los repositorios.")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "*Fuente*: [github.com/anthropics](https://github.com/anthropics)",
        "",
        "*Generado automáticamente*",
    ])
    
    return '\n'.join(lines)


def generate_summary_markdown(date_str: str, research: List[Dict], docs: List[Dict], github: List[Dict]) -> str:
    """Genera markdown resumen de todo."""
    lines = [
        f"# Resumen General - {date_str}",
        "",
        f"**Fecha de generación**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
        "## 📊 Estadísticas del Día",
        "",
    ]
    
    research_count = len([r for r in research if not r.get('error')])
    docs_count = len([d for d in docs if not d.get('error')])
    github_count = len([g for g in github if not g.get('error')])
    
    lines.extend([
        f"- **🔬 Research**: [{research_count} papers](./research/{date_str}.md)",
        f"- **💻 GitHub**: [{github_count} repos con actividad](./github/{date_str}.md)",
        "",
        "---",
        "",
        "## 🔗 Links Rápidos",
        "",
        "- [Anthropic Research](https://www.anthropic.com/research)",
        "- [Claude Docs](https://docs.anthropic.com)",
        "- [Anthropic GitHub](https://github.com/anthropics)",
        "",
        "---",
        "",
        "*Generado automáticamente*",
    ])
    
    return '\n'.join(lines)


def main():
    """Función principal."""
    today = datetime.now().strftime('%Y-%m-%d')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    print(f"🔍 Generando resumen para {today}...")
    print("")
    
    # Inicializar scraper
    scraper = AnthropicScraper(github_token)
    
    # Obtener datos
    print("📄 Scrapeando Research...")
    research = scraper.scrape_research()
    
    print("📚 Scrapeando Docs...")
    docs = scraper.scrape_docs()
    
    print("💻 Obteniendo GitHub updates...")
    github = scraper.get_github_updates()
    
    # Crear carpetas
    os.makedirs('daily/research', exist_ok=True)
    os.makedirs('daily/github', exist_ok=True)
    
    # Generar archivos individuales
    print("📝 Generando archivos...")
    
    # Research - solo si hay papers nuevos
    research_file = f"daily/research/{today}.md"
    if research and not research[0].get('error'):
        if has_new_papers(research, today):
            research_md = generate_research_markdown(today, research)
            with open(research_file, 'w', encoding='utf-8') as f:
                f.write(research_md)
            print(f"  ✅ daily/research/{today}.md ({len(research)} nuevos papers)")
        else:
            print(f"  ⏭️  daily/research/{today}.md (sin papers nuevos, no generado)")
    else:
        print(f"  ⚠️  daily/research/{today}.md (error al obtener datos)")
    
    # GitHub
    github_md = generate_github_markdown(today, github)
    with open(f"daily/github/{today}.md", 'w', encoding='utf-8') as f:
        f.write(github_md)
    print(f"  ✅ daily/github/{today}.md")
    
    # Resumen general
    summary_md = generate_summary_markdown(today, research, docs, github)
    with open(f"daily/{today}.md", 'w', encoding='utf-8') as f:
        f.write(summary_md)
    print(f"  ✅ daily/{today}.md (resumen)")
    
    print("")
    print("✅ Todos los archivos generados")
    
    # Actualizar índice
    update_index()


def has_new_papers(current_papers: List[Dict], today: str) -> bool:
    """Comprueba si hay papers nuevos comparando con el día anterior."""
    import glob
    
    # Buscar archivo de research del día anterior
    research_files = sorted(glob.glob('daily/research/*.md'), reverse=True)
    
    if not research_files:
        return True  # No hay archivos previos, todo es nuevo
    
    # Leer el archivo más reciente que NO sea el de hoy
    previous_file = None
    for f in research_files:
        if today not in f:
            previous_file = f
            break
    
    if not previous_file:
        return True  # No hay archivo previo
    
    try:
        with open(previous_file, 'r', encoding='utf-8') as f:
            previous_content = f.read()
        
        # Extraer URLs de papers del archivo anterior
        import re
        previous_urls = set(re.findall(r'https://www\.anthropic\.com/research/[^\s\)\]]+', previous_content))
        
        # Comprobar si algún paper actual es nuevo
        current_urls = {paper['url'] for paper in current_papers if paper.get('url')}
        
        new_urls = current_urls - previous_urls
        
        if new_urls:
            print(f"    📄 {len(new_urls)} papers nuevos encontrados")
            return True
        else:
            print(f"    📄 Sin papers nuevos (todos ya estaban en {os.path.basename(previous_file)})")
            return False
            
    except Exception as e:
        print(f"    ⚠️ Error comparando con archivo anterior: {e}")
        return True  # En caso de error, generar de todos modos


def update_index():
    """Actualiza el README con índice."""
    try:
        research_files = sorted([f for f in os.listdir('daily/research') if f.endswith('.md')], reverse=True)
        
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        index_start = content.find('## 📅 Histórico')
        if index_start == -1:
            return
        
        index_end = content.find('## ', index_start + 1)
        if index_end == -1:
            index_end = len(content)
        
        new_index = [
            "## 📅 Histórico",
            "",
            "| Fecha | Research | Docs | GitHub | Resumen |",
            "|-------|----------|------|--------|---------|"
        ]
        
        for filename in research_files[:30]:
            date = filename.replace('.md', '')
            new_index.append(
                f"| {date} | "
                f"[Research](./daily/research/{filename}) | "
                f"[Docs](./daily/docs/{filename}) | "
                f"[GitHub](./daily/github/{filename}) | "
                f"[Resumen](./daily/{filename}) |"
            )
        
        new_content = content[:index_start] + '\n'.join(new_index) + '\n\n' + content[index_end:]
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Índice actualizado")
    except Exception as e:
        print(f"⚠️ Error actualizando índice: {e}")


if __name__ == '__main__':
    main()
