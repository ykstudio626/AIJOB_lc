#!/usr/bin/env python3
"""
Google AI Studio パッケージの互換性テストスクリプト
"""

def test_import():
    try:
        # 基本的なインポートテスト
        print("Testing imports...")
        
        import google.generativeai as genai
        print("✓ google.generativeai imported successfully")
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✓ ChatGoogleGenerativeAI imported successfully")
        
        # MediaResolution属性の存在確認
        if hasattr(genai.GenerationConfig, 'MediaResolution'):
            print("✓ MediaResolution attribute exists")
        else:
            print("✗ MediaResolution attribute missing - version mismatch")
            
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except AttributeError as e:
        print(f"✗ Attribute error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = test_import()
    if success:
        print("\n✓ All imports successful - packages are compatible")
    else:
        print("\n✗ Package version incompatibility detected")
        print("Recommended actions:")
        print("1. Check PyPI for compatible versions")
        print("2. Try: pip install google-generativeai==0.7.* langchain-google-genai==2.*")
        print("3. Or use OpenAI as alternative: LLM_PROVIDER=openai")