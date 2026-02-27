# Anthropic Daily Resume

📰 Automated daily summary of Anthropic updates: Research and GitHub.

## 🎯 What's Included Each Day

- **🔬 Research**: New papers and publications from anthropic.com/research
- **💻 GitHub**: Activity in github.com/anthropics repositories (including claude-code changelog)

## 📁 Structure

```
daily/
├── research/           # Research papers daily updates
│   └── YYYY-MM-DD.md
├── github/            # GitHub repositories daily updates
│   └── YYYY-MM-DD.md
└── YYYY-MM-DD.md      # Daily summary (all categories)
```

## 🚀 How It Works

1. **GitHub Actions** runs the scraper daily at 9:00 AM UTC
2. The bot fetches data from 2 sources:
   - Web scraping of Anthropic Research
   - GitHub API for `anthropics` organization (includes claude-code changelog)
3. Generates Markdown summaries in English
4. Auto-commits to the repository

## 🛠️ Technologies

- **Python 3.11**
- **BeautifulSoup4** - Web scraping
- **PyGithub** - GitHub API
- **GitHub Actions** - Automation

## 📅 Historical Archive

| Date | Research | GitHub | Summary |
|------|----------|--------|---------|
<!-- Entries generated automatically -->

## 🔗 Sources

- [Anthropic Research](https://www.anthropic.com/research)
- [Claude Documentation](https://docs.anthropic.com)
- [Anthropic GitHub](https://github.com/anthropics)

## 🌐 Languages

- 🇬🇧 [English](README.md) (Default)
- 🇪🇸 [Español](README.es.md)

## ⚠️ Notes

- Summaries are auto-generated and may contain errors
- Web scraping depends on current website structure (may break)
- GitHub API requires token for unrestricted access

## 📄 License

MIT - Free to use and modify.

---

*Generated automatically by [anthropic-resume-day-to-day](https://github.com/edumesones/anthropic-resume-day-to-day)*
