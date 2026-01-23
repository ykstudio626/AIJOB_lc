# Geminiモデル価格比較（Google AI Studio）

本ドキュメントは、AIJOB_lcシステムで実装されているGoogle AI Studio（Gemini）系の4モデルの価格とパフォーマンス特性を詳細に比較したものです。

## 価格比較表

| モデル | 実装名 | 正式モデル名 | 入力価格（$/100万トークン） | 出力価格（$/100万トークン） | 特徴・用途 |
|--------|--------|-------------|---------------------|---------------------|----------|
| **Gemini Flash Latest** | `gemini_flash` | `gemini-flash-latest` | **$0.30** | **$2.50** | 🚀 最高速・軽量処理向け |
| **Gemini 2.0 Flash** | `gemini_20_flash` | `gemini-2.0-flash` | **$0.10** | **$0.40** | 💰 最コスパ・バランス型 |
| **Gemini 2.5 Flash** | `gemini_25_flash` | `gemini-2.5-flash` | **$0.30** | **$2.50** | ⚡ 思考トークン対応・高性能 |
| **Gemini Pro Latest** | `gemini_pro` | `gemini-pro-latest` | **$1.25** | **$10.00** | 🎯 最高品質・複雑処理向け |

## 価格差の詳細分析

### 最も安価：Gemini 2.0 Flash
- **入力**: $0.10/100万トークン（他モデルの1/3〜1/12.5）
- **出力**: $0.40/100万トークン（他モデルの1/6.25〜1/25）
- **総コスト削減効果**: 約60-90%
- **特徴**: 最もバランスの取れたコストパフォーマンス

### 最も高価：Gemini Pro Latest
- **入力**: $1.25/100万トークン（2.0 Flashの12.5倍）
- **出力**: $10.00/100万トークン（2.0 Flashの25倍）
- **価値提供**: 高品質・複雑処理での最高レベルの精度
- **用途**: ビジネスクリティカルな案件マッチング

### 速度重視：Gemini Flash Latest & 2.5 Flash
- **同価格帯**: $0.30/$2.50
- **差別化要因**:
  - Flash Latest: 最高速度に最適化
  - 2.5 Flash: 思考トークン対応でより高性能

## 実装における使い分け

### 環境変数設定例

```bash
# コスト最適化設定（推奨：日常業務）
export LLM_PROVIDER=ai_studio
export LLM_MODEL=gemini_20_flash  # 60-90%コスト削減

# 速度最適化設定（推奨：リアルタイム処理）
export LLM_PROVIDER=ai_studio
export LLM_MODEL=gemini_flash    # 最高速処理

# 品質最優先設定（推奨：重要案件）
export LLM_PROVIDER=ai_studio  
export LLM_MODEL=gemini_pro     # 最高品質
```

### 利用シナリオ別推奨

| シナリオ | 推奨モデル | 理由 | コスト効率 |
|----------|------------|------|------------|
| **日常的な案件マッチング** | Gemini 2.0 Flash | 最高のコストパフォーマンス | ⭐⭐⭐⭐⭐ |
| **リアルタイム応答** | Gemini Flash Latest | 最高速度での処理 | ⭐⭐⭐⭐ |
| **複雑な要件分析** | Gemini 2.5 Flash | 思考トークンによる詳細分析 | ⭐⭐⭐ |
| **ビジネスクリティカル** | Gemini Pro Latest | 最高品質の結果保証 | ⭐⭐ |

## パフォーマンステスト結果

### 処理時間比較（参考値）

```bash
# OpenAI GPT-4o-mini（ベースライン）
time: 30.332s total (0.69s user, 0.21s system, 2% cpu)

# 期待されるGemini改善値
Gemini Flash Latest: 15-20s total (50-70%短縮予想)
Gemini 2.0 Flash: 18-25s total (40-60%短縮予想)
```

### クォータ制限について

**無料ティア制限**
- Gemini 2.0 Flash: 無料枠でのクォータ制限あり
- Gemini Flash Latest: 無料利用可能
- 本格運用時は有料プランへの移行を推奨

## 統合システムでの活用

現在のAIJOB_lcシステムでは、`llm_config.py`での統一設定により、環境変数でのプロバイダー・モデル切り替えが可能です。

### 動的モデル選択の実装可能性

```python
# 将来的な実装案: ワークロード別自動選択
def select_optimal_model(workload_type, priority):
    if priority == "cost":
        return "gemini_20_flash"
    elif priority == "speed":
        return "gemini_flash"
    elif priority == "quality":
        return "gemini_pro"
    else:
        return "gemini_25_flash"  # バランス型
```

## まとめ

- **最推奨**: Gemini 2.0 Flash（コスト効率No.1）
- **速度重視**: Gemini Flash Latest
- **品質重視**: Gemini Pro Latest
- **バランス型**: Gemini 2.5 Flash

本システムの柔軟な設計により、用途に応じた最適なコスト・性能バランスの選択が可能です。

---

*最終更新: 2026年1月23日*
*データソース: Google AI Studio公式料金表*