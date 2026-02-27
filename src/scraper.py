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
        """Obtiene papers de research de Anthropic."""
        url = "https://www.anthropic.com/research"
        papers = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            selectors = [
                'article', '.research-item', '.publication', 
                '[data-testid="research-card"]',
                '.post', '.blog-post'
            ]
            
            items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    break
            
            for item in items[:10]:
                try:
                    title_elem = item.select_one('h2, h3, .title, [data-testid="title"]')
                    title = title_elem.get_text(strip=True) if title_elem else "Sin título"
                    
                    desc_elem = item.select_one('p, .description, .excerpt')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    link_elem = item.select_one('a[href]')
                    link = ""
                    if link_elem:
                        href = link_elem.get('href', '')
                        link = f"https://www.anthropic.com{href}" if href.startswith('/') else href
                    
                    date_elem = item.select_one('time, .date, [datetime]')
                    date_str = ""
                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    
                    papers.append({
                        'title': title,
                        'description': description[:300] + "..." if len(description) > 300 else description,
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
                'message': f"No se pudo obtener research: {str(e)}",
                'url': url
            })
        
        return papers
    
    def scrape_docs(self) -> List[Dict]:
        """Obtiene cambios recientes en documentación."""
        urls = [
            "https://docs.anthropic.com/en/api/changelog",
            "https://docs.anthropic.com/en/release-notes",
            "https://docs.anthropic.com/en/home"
        ]
        
        updates = []
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                sections = soup.select('h2, h3, .changelog-item, .update')[:5]
                
                for section in sections:
                    try:
                        title = section.get_text(strip=True)
                        next_p = section.find_next('p')
                        description = next_p.get_text(strip=True) if next_p else ""
                        
                        updates.append({
                            'title': title,
                            'description': description[:250] + "..." if len(description) > 250 else description,
                            'url': url,
                            'type': 'documentation',
                            'source': 'docs.anthropic.com'
                        })
                    except:
                        continue
                
                if updates:
                    break
                    
            except Exception as e:
                print(f"Error con {url}: {e}")
                continue
        
        if not updates:
            updates.append({
                'error': True,
                'message': 'No se pudieron obtener actualizaciones de documentación',
                'suggestion': 'Visitar https://docs.anthropic.com/en/api/changelog manualmente'
            })
        
        return updates
    
    def get_github_updates(self, org_name: str = "anthropics") -> List[Dict]:
        """Obtiene actualizaciones de repos de Anthropic en GitHub."""
        if not self.github:
            return [{
                'error': True,
                'message': 'GitHub token no configurado'
            }]
        
        updates = []
        yesterday = datetime.now() - timedelta(days=1)
        
        try:
            org = self.github.get_organization(org_name)
            repos = org.get_repos(type='public', sort='updated')
            
            for repo in repos[:20]:
                try:
                    if repo.updated_at < yesterday:
                        continue
                    
                    commits = repo.get_commits(since=yesterday)
                    recent_commits = list(commits[:3])
                    
                    releases = repo.get_releases()
                    recent_release = None
                    try:
                        for release in releases:
                            if release.created_at > yesterday:
                                recent_release = release
                                break
                    except:
                        pass
                    
                    if recent_commits or recent_release:
                        update_info = {
                            'name': repo.name,
                            'url': repo.html_url,
                            'description': repo.description or "Sin descripción",
                            'stars': repo.stargazers_count,
                            'language': repo.language,
                            'updated_at': repo.updated_at.isoformat(),
                            'commits': [],
                            'release': None
                        }
                        
                        for commit in recent_commits:
                            update_info['commits'].append({
                                'message': commit.commit.message.split('\n')[0],
                                'url': commit.html_url,
                                'author': commit.commit.author.name,
                                'date': commit.commit.author.date.isoformat()
                            })
                        
                        if recent_release:
                            update_info['release'] = {
                                'tag': recent_release.tag_name,
                                'name': recent_release.title,
                                'url': recent_release.html_url,
                                'body': recent_release.body[:500] + "..." if recent_release.body and len(recent_release.body) > 500 else (recent_release.body or "")
                            }
                        
                        updates.append(update_info)
                        
                except Exception as e:
                    print(f"Error procesando repo {repo.name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error accediendo a GitHub: {e}")
            updates.append({
                'error': True,
                'message': f'Error accediendo a GitHub: {str(e)}'
            })
        
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
    """Genera markdown solo para Docs."""
    lines = [
        f"# Documentación - {date_str}",
        "",
        f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
    ]
    
    if docs and not docs[0].get('error'):
        lines.append(f"## Actualizaciones encontradas: {len(docs)}")
        lines.append("")
        
        for doc in docs[:10]:
            lines.extend([
                f"### [{doc['title']}]({doc['url']})",
                "",
            ])
            if doc.get('description'):
                lines.append(doc['description'])
                lines.append("")
            lines.append(f"**Link**: [{doc['url']}]({doc['url']})")
            lines.append("")
            lines.append("---")
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
        "*Fuente*: [docs.anthropic.com](https://docs.anthropic.com)",
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
        lines.append(f"## Repositorios con actividad: {len(repos)}")
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
            
            if repo.get('commits'):
                lines.append("**Commits recientes**:")
                lines.append("")
                for commit in repo['commits'][:3]:
                    msg = commit.get('message', '')[:80]
                    if len(commit.get('message', '')) > 80:
                        msg += "..."
                    lines.append(f"- [{msg}]({commit['url']})")
                lines.append("")
            
            if repo.get('release'):
                release = repo['release']
                lines.append(f"**Release**: [{release['tag']} - {release['name']}]({release['url']})")
                lines.append("")
                if release.get('body'):
                    body = release['body'][:200].replace('\n', ' ')
                    lines.append(f"> {body}...")
                    lines.append("")
            
            score, reasons = scraper.calculate_utility(repo)
            stars = "⭐" * score
            lines.append(f"**Utilidad**: {stars} ({score}/5)")
            if reasons:
                lines.append(f"- {', '.join(reasons)}")
            lines.append("")
            
            lines.append(f"**Link**: [Ver en GitHub]({repo['url']})")
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
        f"- **📚 Docs**: [{docs_count} actualizaciones](./docs/{date_str}.md)",
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
    os.makedirs('daily/docs', exist_ok=True)
    os.makedirs('daily/github', exist_ok=True)
    
    # Generar archivos individuales
    print("📝 Generando archivos...")
    
    # Research
    research_md = generate_research_markdown(today, research)
    with open(f"daily/research/{today}.md", 'w', encoding='utf-8') as f:
        f.write(research_md)
    print(f"  ✅ daily/research/{today}.md")
    
    # Docs
    docs_md = generate_docs_markdown(today, docs)
    with open(f"daily/docs/{today}.md", 'w', encoding='utf-8') as f:
        f.write(docs_md)
    print(f"  ✅ daily/docs/{today}.md")
    
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
