"""
RAG（Retrieval-Augmented Generation）サンプルコード
検索拡張生成システムの実装例

必要なライブラリのインストール:
pip install langchain openai chromadb tiktoken pypdf sentence-transformers
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib

# LangChainのインポート
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# 追加のユーティリティ
import numpy as np
from datetime import datetime


@dataclass
class RAGConfig:
    """RAGシステムの設定"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    temperature: float = 0.7
    model_name: str = "gpt-3.5-turbo"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    persist_directory: str = "./chroma_db"


class SimpleRAGSystem:
    """
    シンプルなRAGシステムの実装
    ローカルで動作可能な軽量版
    """
    
    def __init__(self, config: RAGConfig = None):
        """
        RAGシステムの初期化
        
        Args:
            config: RAG設定オブジェクト
        """
        self.config = config or RAGConfig()
        self.documents = []
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None
        
        # エンベディングモデルの初期化（HuggingFaceの無料モデル使用）
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model,
            model_kwargs={'device': 'cpu'}
        )
        
        print(f"✅ RAGシステムを初期化しました")
        print(f"   - チャンクサイズ: {self.config.chunk_size}")
        print(f"   - エンベディングモデル: {self.config.embedding_model}")
    
    def load_documents(self, texts: List[str], metadata: List[Dict] = None):
        """
        テキストドキュメントをロード
        
        Args:
            texts: テキストのリスト
            metadata: 各テキストのメタデータ
        """
        if metadata is None:
            metadata = [{"source": f"document_{i}"} for i in range(len(texts))]
        
        # ドキュメントオブジェクトの作成
        self.documents = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(texts, metadata)
        ]
        
        print(f"📄 {len(self.documents)}個のドキュメントをロードしました")
        
        # テキストの分割
        self._split_documents()
    
    def _split_documents(self):
        """ドキュメントをチャンクに分割"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "、", " ", ""]
        )
        
        split_docs = text_splitter.split_documents(self.documents)
        self.documents = split_docs
        
        print(f"✂️  {len(split_docs)}個のチャンクに分割しました")
    
    def create_vector_store(self):
        """ベクトルストアを作成"""
        print("🔄 ベクトルストアを作成中...")
        
        # Chromaベクトルストアの作成
        self.vector_store = Chroma.from_documents(
            documents=self.documents,
            embedding=self.embeddings,
            persist_directory=self.config.persist_directory
        )
        
        # 永続化
        self.vector_store.persist()
        
        # リトリーバーの設定
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.config.top_k}
        )
        
        print(f"✅ ベクトルストアを作成しました（{len(self.documents)}個のベクトル）")
    
    def search(self, query: str, k: int = None) -> List[Document]:
        """
        類似度検索を実行
        
        Args:
            query: 検索クエリ
            k: 返す文書の数
        
        Returns:
            関連文書のリスト
        """
        if self.vector_store is None:
            raise ValueError("ベクトルストアが作成されていません")
        
        k = k or self.config.top_k
        results = self.vector_store.similarity_search(query, k=k)
        
        return results
    
    def search_with_score(self, query: str, k: int = None) -> List[tuple]:
        """
        スコア付きで類似度検索を実行
        
        Args:
            query: 検索クエリ
            k: 返す文書の数
        
        Returns:
            (文書, スコア)のタプルのリスト
        """
        if self.vector_store is None:
            raise ValueError("ベクトルストアが作成されていません")
        
        k = k or self.config.top_k
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        return results
    
    def generate_answer(self, query: str, context: List[str]) -> str:
        """
        コンテキストを基に回答を生成（シンプル版）
        
        Args:
            query: 質問
            context: 関連文書のリスト
        
        Returns:
            生成された回答
        """
        # プロンプトテンプレート
        prompt_template = """
以下の情報を基に質問に答えてください。
情報にない内容については、「提供された情報には含まれていません」と回答してください。

コンテキスト:
{context}

質問: {question}

回答: """
        
        # コンテキストの結合
        context_text = "\n\n".join(context)
        
        # プロンプトの作成
        prompt = prompt_template.format(
            context=context_text,
            question=query
        )
        
        # 実際のLLM呼び出しの代わりに、デモ用の回答を生成
        # 本番環境では、ここでOpenAI APIやローカルLLMを呼び出します
        demo_answer = f"""
質問「{query}」に対する回答：

提供されたコンテキストに基づいて、以下の情報が見つかりました：
- {len(context)}個の関連文書から情報を抽出
- 最も関連性の高い情報: {context[0][:100]}...

[注意: これはデモ用の回答です。実際の実装では、LLMが適切な回答を生成します]
"""
        
        return demo_answer
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        RAGパイプライン全体を実行
        
        Args:
            question: ユーザーの質問
        
        Returns:
            回答と関連情報を含む辞書
        """
        print(f"\n🔍 質問: {question}")
        
        # 1. 関連文書の検索
        relevant_docs = self.search_with_score(question)
        
        # 2. コンテキストの抽出
        context = [doc.page_content for doc, score in relevant_docs]
        scores = [float(score) for doc, score in relevant_docs]
        
        # 3. 回答の生成
        answer = self.generate_answer(question, context)
        
        # 4. 結果の構築
        result = {
            "question": question,
            "answer": answer,
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                }
                for doc, score in relevant_docs
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return result


class AdvancedRAGSystem(SimpleRAGSystem):
    """
    高度なRAGシステムの実装
    追加機能: リランキング、ハイブリッド検索、クエリ拡張
    """
    
    def __init__(self, config: RAGConfig = None):
        super().__init__(config)
        self.query_history = []
        self.feedback_data = []
    
    def expand_query(self, query: str) -> List[str]:
        """
        クエリ拡張：同義語や関連語を追加
        
        Args:
            query: 元のクエリ
        
        Returns:
            拡張されたクエリのリスト
        """
        # シンプルな実装例
        expanded_queries = [query]
        
        # 簡単な同義語辞書（実際は外部APIや辞書を使用）
        synonyms = {
            "RAG": ["Retrieval Augmented Generation", "検索拡張生成"],
            "エージェント": ["Agent", "自律システム"],
            "AI": ["人工知能", "Artificial Intelligence"],
        }
        
        # クエリ内の単語を同義語で置換
        for word, syns in synonyms.items():
            if word in query:
                for syn in syns:
                    expanded_queries.append(query.replace(word, syn))
        
        return expanded_queries
    
    def hybrid_search(self, query: str, k: int = None) -> List[Document]:
        """
        ハイブリッド検索：密ベクトル検索とキーワード検索の組み合わせ
        
        Args:
            query: 検索クエリ
            k: 返す文書の数
        
        Returns:
            関連文書のリスト
        """
        k = k or self.config.top_k
        
        # 1. 密ベクトル検索
        vector_results = self.search(query, k=k*2)
        
        # 2. キーワード検索（シンプルな実装）
        keywords = query.lower().split()
        keyword_scores = []
        
        for doc in self.documents:
            score = sum(
                1 for keyword in keywords 
                if keyword in doc.page_content.lower()
            )
            if score > 0:
                keyword_scores.append((doc, score))
        
        # スコアでソート
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        keyword_results = [doc for doc, _ in keyword_scores[:k*2]]
        
        # 3. 結果の統合とリランキング
        combined_results = []
        seen_contents = set()
        
        # ベクトル検索結果を優先
        for doc in vector_results:
            doc_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            if doc_hash not in seen_contents:
                combined_results.append(doc)
                seen_contents.add(doc_hash)
        
        # キーワード検索結果を追加
        for doc in keyword_results:
            doc_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            if doc_hash not in seen_contents and len(combined_results) < k:
                combined_results.append(doc)
                seen_contents.add(doc_hash)
        
        return combined_results[:k]
    
    def rerank_results(self, query: str, documents: List[Document]) -> List[Document]:
        """
        検索結果のリランキング
        
        Args:
            query: 元のクエリ
            documents: 検索結果の文書リスト
        
        Returns:
            リランキングされた文書リスト
        """
        # クロスエンコーダーやより高度なスコアリングを実装
        # ここでは簡単な実装例
        
        scored_docs = []
        query_terms = set(query.lower().split())
        
        for doc in documents:
            # スコア計算（クエリとの関連度）
            doc_terms = set(doc.page_content.lower().split())
            
            # Jaccard類似度
            intersection = query_terms.intersection(doc_terms)
            union = query_terms.union(doc_terms)
            jaccard_score = len(intersection) / len(union) if union else 0
            
            # 文書長によるペナルティ（短すぎる・長すぎる文書を避ける）
            length_penalty = 1.0
            doc_length = len(doc.page_content)
            if doc_length < 50:
                length_penalty = 0.5
            elif doc_length > 2000:
                length_penalty = 0.8
            
            final_score = jaccard_score * length_penalty
            scored_docs.append((doc, final_score))
        
        # スコアでソート
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, _ in scored_docs]
    
    def query_with_feedback(self, question: str, use_feedback: bool = True) -> Dict[str, Any]:
        """
        フィードバックを考慮したクエリ実行
        
        Args:
            question: ユーザーの質問
            use_feedback: フィードバックを使用するか
        
        Returns:
            回答と関連情報を含む辞書
        """
        # クエリ拡張
        expanded_queries = self.expand_query(question)
        
        # ハイブリッド検索
        all_results = []
        for eq in expanded_queries:
            results = self.hybrid_search(eq)
            all_results.extend(results)
        
        # 重複除去
        unique_results = []
        seen = set()
        for doc in all_results:
            doc_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            if doc_hash not in seen:
                unique_results.append(doc)
                seen.add(doc_hash)
        
        # リランキング
        reranked_results = self.rerank_results(question, unique_results)
        
        # 上位k件を選択
        final_results = reranked_results[:self.config.top_k]
        
        # コンテキスト抽出と回答生成
        context = [doc.page_content for doc in final_results]
        answer = self.generate_answer(question, context)
        
        # 履歴に追加
        self.query_history.append({
            "question": question,
            "timestamp": datetime.now().isoformat()
        })
        
        result = {
            "question": question,
            "answer": answer,
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in final_results
            ],
            "expanded_queries": expanded_queries,
            "search_method": "hybrid",
            "timestamp": datetime.now().isoformat()
        }
        
        return result


# ========================================
# 使用例とデモンストレーション
# ========================================

def demo_simple_rag():
    """シンプルなRAGシステムのデモ"""
    print("=" * 60)
    print("🚀 シンプルRAGシステムのデモ")
    print("=" * 60)
    
    # サンプルドキュメント
    sample_documents = [
        """RAG（Retrieval-Augmented Generation）は、大規模言語モデル（LLM）の
        能力を拡張する技術です。外部の知識ベースから関連情報を検索し、
        その情報を基に回答を生成することで、より正確で最新の情報を提供できます。""",
        
        """AIエージェントは、特定の目標を達成するために自律的に動作する
        ソフトウェアシステムです。環境を認識し、計画を立て、行動を実行する
        能力を持ちます。""",
        
        """ベクトルデータベースは、高次元ベクトルデータを効率的に保存し、
        類似度検索を高速に実行するための特殊なデータベースです。
        Chroma、Pinecone、Weaviateなどが代表的な例です。""",
        
        """プロンプトエンジニアリングは、AIモデルから望ましい出力を得るために、
        入力プロンプトを最適化する技術です。Few-shot学習やChain of Thought
        などの手法があります。""",
        
        """LangChainは、LLMアプリケーション開発のためのフレームワークです。
        チェーン、エージェント、メモリ、ツールなどの概念を提供し、
        複雑なAIアプリケーションの構築を容易にします。"""
    ]
    
    # メタデータの追加
    metadata = [
        {"source": "rag_basics.pdf", "page": 1},
        {"source": "ai_agents.pdf", "page": 5},
        {"source": "vector_db_guide.pdf", "page": 3},
        {"source": "prompt_engineering.pdf", "page": 2},
        {"source": "langchain_docs.pdf", "page": 10}
    ]
    
    # RAGシステムの初期化
    rag = SimpleRAGSystem()
    
    # ドキュメントのロード
    rag.load_documents(sample_documents, metadata)
    
    # ベクトルストアの作成
    rag.create_vector_store()
    
    # 質問応答のテスト
    test_questions = [
        "RAGとは何ですか？",
        "AIエージェントの特徴を教えてください",
        "ベクトルデータベースの例を挙げてください"
    ]
    
    for question in test_questions:
        print("\n" + "=" * 40)
        result = rag.query(question)
        
        print(f"📌 質問: {result['question']}")
        print(f"💬 回答:\n{result['answer'][:200]}...")
        print(f"📚 参照した文書数: {len(result['source_documents'])}")
        
        # 最も関連性の高い文書を表示
        if result['source_documents']:
            top_doc = result['source_documents'][0]
            print(f"📄 最も関連性の高い文書:")
            print(f"   - ソース: {top_doc['metadata'].get('source', 'N/A')}")
            print(f"   - スコア: {top_doc.get('similarity_score', 'N/A'):.3f}")


def demo_advanced_rag():
    """高度なRAGシステムのデモ"""
    print("\n" + "=" * 60)
    print("🚀 高度なRAGシステムのデモ")
    print("=" * 60)
    
    # サンプルドキュメント（より詳細）
    advanced_documents = [
        """機械学習における教師あり学習は、ラベル付きデータを使用してモデルを訓練する手法です。
        分類問題と回帰問題が主な応用例で、決定木、ランダムフォレスト、
        サポートベクターマシン、ニューラルネットワークなどのアルゴリズムが使用されます。""",
        
        """深層学習は、多層のニューラルネットワークを使用する機械学習の一分野です。
        CNN（畳み込みニューラルネットワーク）は画像認識に、
        RNN（再帰型ニューラルネットワーク）は時系列データに、
        Transformerは自然言語処理に特に効果的です。""",
        
        """自然言語処理（NLP）は、人間の言語をコンピュータで処理する技術です。
        トークン化、品詞タグ付け、固有表現認識、感情分析、機械翻訳、
        質問応答システムなど、様々なタスクが含まれます。""",
        
        """強化学習は、エージェントが環境との相互作用を通じて最適な行動を学習する手法です。
        Q学習、SARSA、Deep Q-Network（DQN）、Policy Gradient、
        Actor-Criticなどのアルゴリズムがあります。"""
    ]
    
    # 高度なRAGシステムの初期化
    advanced_rag = AdvancedRAGSystem()
    
    # ドキュメントのロード
    advanced_rag.load_documents(advanced_documents)
    
    # ベクトルストアの作成
    advanced_rag.create_vector_store()
    
    # クエリ拡張とハイブリッド検索のテスト
    test_query = "深層学習のアルゴリズムについて教えてください"
    
    print(f"\n📝 元のクエリ: {test_query}")
    
    # クエリ拡張
    expanded = advanced_rag.expand_query(test_query)
    print(f"📈 拡張されたクエリ: {expanded}")
    
    # ハイブリッド検索の実行
    result = advanced_rag.query_with_feedback(test_query)
    
    print(f"\n💬 回答:\n{result['answer'][:300]}...")
    print(f"🔍 検索方法: {result['search_method']}")
    print(f"📚 参照した文書数: {len(result['source_documents'])}")


def save_rag_results(results: Dict[str, Any], filename: str = "rag_results.json"):
    """RAGの結果をファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果を {filename} に保存しました")


# ========================================
# メイン実行部分
# ========================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     RAG (Retrieval-Augmented Generation) Demo        ║
    ║          検索拡張生成システムのサンプル                  ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # シンプルなRAGのデモ
    demo_simple_rag()
    
    # 高度なRAGのデモ
    demo_advanced_rag()
    
    print("\n" + "=" * 60)
    print("✅ デモンストレーション完了！")
    print("=" * 60)
    
    # カスタム使用例
    print("\n📘 カスタム使用例:")
    print("""
    # あなたのコードでRAGを使用する例:
    
    from rag_sample import SimpleRAGSystem
    
    # 初期化
    rag = SimpleRAGSystem()
    
    # あなたのドキュメントをロード
    my_documents = ["文書1の内容", "文書2の内容", ...]
    rag.load_documents(my_documents)
    
    # ベクトルストアを作成
    rag.create_vector_store()
    
    # 質問応答
    result = rag.query("あなたの質問")
    print(result['answer'])
    """)
    
    print("\n🎉 RAGシステムを使って、知識ベースを活用した")
    print("   高度な質問応答システムを構築してください！")
