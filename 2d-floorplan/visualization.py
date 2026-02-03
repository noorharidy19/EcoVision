import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
import requests
import time
import os

# --- ⚙️ الإعدادات الأساسية ---
DXF_FILE = "/kaggle/input/test-dxf/Drawing 1.dxf" # مسار ملف الـ DXF
API_KEY = ""
OUTPUT_PNG = "floorplan_sketch.png"
FINAL_RENDER_NAME = "final_3d_render.png"

# --- 🎨 1. دالة تحويل DXF لـ PNG ---
def convert_dxf_to_png(dxf_path, output_path):
    print("🎨 Step 1: Converting DXF to PNG...")
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        fig = plt.figure(figsize=(15, 15))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp, finalize=True)
        # DPI 150 هو التوازن المثالي بين السرعة والجودة
        plt.savefig(output_path, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"✅ PNG Created successfully: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Conversion Error: {e}")
        return False

# --- 🤖 2. دالة التعامل مع الـ AI (الرفع والمتابعة) ---
def process_with_mnml(image_path, api_key):
    upload_url = "https://api.mnmlai.dev/v1/archDiffusion-v42"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    data = {
        "prompt": "high-end modern apartment floorplan, realistic materials, 3d render, wooden floors, luxury furniture",
        "expert_name": "plan", # عشان الـ AI يفهم إنه بلان معماري
        "render_style": "photoreal"
    }

    try:
        # أ- عملية الرفع
        with open(image_path, "rb") as img_file:
            files = {'image': (image_path, img_file, 'image/png')}
            print("🚀 Step 2: Uploading to Mnml AI...")
            response = requests.post(upload_url, headers=headers, files=files, data=data)
            
        if response.status_code == 200:
            task_id = response.json().get("id")
            print(f"✅ Task started! ID: {task_id}")
            
            # ب- عملية المتابعة الأوتوماتيكية (Polling)
            status_url = f"https://api.mnmlai.dev/v1/status/{task_id}"
            print("⏳ Step 3: AI is rendering... please wait.")
            
            while True:
                status_res = requests.get(status_url, headers=headers)
                if status_res.status_code == 200:
                    status_data = status_res.json()
                    
                    if status_data.get("status") == "succeeded":
                        image_url = status_data.get("outputs")[0]
                        print("\n✨ SUCCESS! Rendering finished.")
                        print(f"🔗 Image Link: {image_url}")
                        
                        # ج- حفظ الصورة أوتوماتيكياً
                        img_data = requests.get(image_url).content
                        with open(FINAL_RENDER_NAME, 'wb') as handler:
                            handler.write(img_data)
                        print(f"💾 Image saved locally as: {FINAL_RENDER_NAME}")
                        return image_url
                    
                    elif status_data.get("status") == "failed":
                        print(f"\n❌ AI Failed: {status_data.get('message')}")
                        return None
                    
                    print(".", end="", flush=True) # نقطة انتظار
                time.sleep(5)
        else:
            print(f"❌ API Error: {response.text}")
    except Exception as e:
        print(f"❌ Request Error: {e}")

# --- 🏁 3. التشغيل ---
if __name__ == "__main__":
    if convert_dxf_to_png(DXF_FILE, OUTPUT_PNG):
        process_with_mnml(OUTPUT_PNG, API_KEY)