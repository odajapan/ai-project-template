# Template Improvements Roadmap

このドキュメントはテンプレートリポジトリの改善計画と進捗を追跡します。
ブランチ: `claude/kind-brown-4444ab`

---

## 凡例
- [ ] 未着手
- [~] 進行中
- [x] 完了

---

## Phase 1 — 既存問題の修正

既存コードの不整合・バグを修正する。

| # | タスク | 状態 |
|---|--------|------|
| 1-1 | `src/__init__.py` 削除（`src/` 自体がパッケージとして誤認識される問題） | [x] |
| 1-2 | flake8 設定を `pyproject.toml` に一本化（`.flake8` 削除） | [x] |
| 1-3 | `test_environment.py` を Python 3.12+ チェックに強化 | [x] |
| 1-4 | `data/` ディレクトリ構造を追加（`.gitkeep`）してREADME・Makefileと整合 | [x] |
| 1-5 | `src/your_project_name/data/make_dataset.py` を追加して `make data` を修正 | [x] |
| 1-6 | `make check` に `typecheck` (mypy) を追加 | [x] |

---

## Phase 2 — Claude Code 対応

Claude Code を使った開発フローをファーストクラスに。

| # | タスク | 状態 |
|---|--------|------|
| 2-1 | `CLAUDE.md` 作成（プロジェクト構造・make コマンド・規約をClaude Codeに伝える） | [x] |
| 2-2 | `.claude/settings.json` 追加（許可ツール・フック設定） | [x] |
| 2-3 | `.env.example` 追加（`ANTHROPIC_API_KEY` など環境変数テンプレート） | [x] |
| 2-4 | `pyproject.toml` に `claude` extra 追加（`anthropic>=0.40` SDK） | [x] |

---

## Phase 3 — Claude API 統合例

新規プロジェクトがすぐに Claude API を使い始められる雛形を提供。

| # | タスク | 状態 |
|---|--------|------|
| 3-1 | `src/your_project_name/llm.py` 追加（プロンプトキャッシング付き Claude API ラッパー） | [x] |
| 3-2 | `tests/test_llm.py` 追加（モックを使った API ラッパーテスト） | [x] |

---

## Phase 4 — 開発体験向上

モダンなツールに統一し、CI を強化する。

| # | タスク | 状態 |
|---|--------|------|
| 4-1 | `ruff` 導入（flake8 + isort + black を置き換え） | [x] |
| 4-2 | `pre-commit` に `mypy` フックを追加 | [x] |
| 4-3 | CI を Python 3.12 / 3.13 マトリクスに拡張 | [x] |
| 4-4 | README に `uv` を使った環境構築手順を追加 | [x] |

---

## Phase 5 — テンプレート完成度

細部の品質を上げる。

| # | タスク | 状態 |
|---|--------|------|
| 5-1 | `rename_project.sh` を改善（`.flake8` 削除対応・`Dockerfile` 対象化・インデント修正） | [x] |
| 5-2 | `requirements-dev.txt` / `requirements-extras.txt` 削除（`pyproject.toml` に一元化済み） | [x] |
| 5-3 | README のプロジェクト構造図を実際のファイル構成に合わせて更新 | [x] |

---

## 進捗サマリー

| Phase | 完了 / 合計 |
|-------|-------------|
| Phase 1 | 6 / 6 ✅ |
| Phase 2 | 4 / 4 ✅ |
| Phase 3 | 2 / 2 ✅ |
| Phase 4 | 4 / 4 ✅ |
| Phase 5 | 3 / 3 ✅ |
| **合計** | **19 / 19 ✅** |
