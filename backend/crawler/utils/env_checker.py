"""
环境检测脚本 - 检测并自动安装MediaCrawler所需依赖
"""
import sys
import subprocess
from pathlib import Path


class EnvironmentChecker:
    def __init__(self):
        self.results = {}
    
    def check_python_version(self) -> bool:
        version = sys.version_info
        is_valid = version.major == 3 and version.minor >= 8
        self.results['python_version'] = {
            'valid': is_valid,
            'version': f"{version.major}.{version.minor}.{version.micro}",
            'message': "Python版本符合要求（3.8+）" if is_valid else "Python版本不符合要求，需要3.8+"
        }
        return is_valid
    
    def check_playwright(self) -> bool:
        try:
            import playwright
            is_valid = True
            version = playwright.__version__
            message = f"Playwright已安装（版本：{version}）"
        except ImportError:
            is_valid = False
            version = None
            message = "Playwright未安装"
        
        self.results['playwright'] = {
            'valid': is_valid,
            'version': version,
            'message': message
        }
        return is_valid
    
    def check_tenacity(self) -> bool:
        try:
            import tenacity
            is_valid = True
            version = tenacity.__version__
            message = f"tenacity已安装（版本：{version}）"
        except ImportError:
            is_valid = False
            version = None
            message = "tenacity未安装"
        
        self.results['tenacity'] = {
            'valid': is_valid,
            'version': version,
            'message': message
        }
        return is_valid
    
    def check_aiofiles(self) -> bool:
        try:
            import aiofiles
            is_valid = True
            version = aiofiles.__version__
            message = f"aiofiles已安装（版本：{version}）"
        except ImportError:
            is_valid = False
            version = None
            message = "aiofiles未安装"
        
        self.results['aiofiles'] = {
            'valid': is_valid,
            'version': version,
            'message': message
        }
        return is_valid
    
    def check_media_crawler(self) -> bool:
        media_crawler_path = Path(__file__).parent.parent / "MediaCrawler"
        is_valid = (
            media_crawler_path.exists() and
            (media_crawler_path / "main.py").exists() and
            (media_crawler_path / "config").exists() and
            (media_crawler_path / "media_platform").exists()
        )
        
        self.results['media_crawler'] = {
            'valid': is_valid,
            'path': str(media_crawler_path),
            'message': "MediaCrawler框架完整" if is_valid else "MediaCrawler框架不完整"
        }
        return is_valid
    
    def check_browser_driver(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            is_valid = True
            message = "Chromium浏览器驱动已安装"
        except Exception as e:
            is_valid = False
            message = f"Chromium浏览器驱动未安装或异常：{str(e)}"
        
        self.results['browser_driver'] = {
            'valid': is_valid,
            'message': message
        }
        return is_valid
    
    def install_dependencies(self) -> bool:
        print("正在安装依赖...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", 
                 "playwright==1.48.0", 
                 "tenacity==8.5.0", 
                 "aiofiles==24.1.0"],
                check=True
            )
            print("✅ Python依赖安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Python依赖安装失败：{e}")
            return False
    
    def install_browser_driver(self) -> bool:
        print("正在安装浏览器驱动...")
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True
            )
            print("✅ Chromium浏览器驱动安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Chromium浏览器驱动安装失败：{e}")
            return False
    
    def check_all(self) -> dict:
        print("=" * 50)
        print("MediaCrawler环境检测")
        print("=" * 50)
        
        self.check_python_version()
        self.check_playwright()
        self.check_tenacity()
        self.check_aiofiles()
        self.check_media_crawler()
        
        print("\n检测结果：")
        for name, result in self.results.items():
            status = "✅" if result['valid'] else "❌"
            print(f"{status} {result['message']}")
        
        all_valid = all(r['valid'] for r in self.results.values())
        
        if all_valid:
            print("\n✅ 所有环境检测通过！")
        else:
            print("\n❌ 部分环境检测未通过，请安装缺失的依赖")
        
        return {
            'all_valid': all_valid,
            'results': self.results
        }
    
    def auto_install(self) -> bool:
        print("\n开始自动安装...")
        
        success = True
        
        if not self.results.get('playwright', {}).get('valid', False):
            if not self.install_dependencies():
                success = False
        
        if not self.results.get('browser_driver', {}).get('valid', False):
            if not self.install_browser_driver():
                success = False
        
        if success:
            print("\n✅ 自动安装完成！")
        else:
            print("\n❌ 自动安装失败，请手动安装")
        
        return success


def check_environment():
    checker = EnvironmentChecker()
    return checker.check_all()


def auto_install_environment():
    checker = EnvironmentChecker()
    checker.check_all()
    return checker.auto_install()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MediaCrawler环境检测与安装")
    parser.add_argument("--install", action="store_true", help="自动安装缺失的依赖")
    args = parser.parse_args()
    
    if args.install:
        auto_install_environment()
    else:
        check_environment()
