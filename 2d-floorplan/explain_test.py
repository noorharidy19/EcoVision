# import requests
# import os

# URL = "https://kennedy-footed-epexegetically.ngrok-free.dev/analyze_dxf"
# file_path = "C:\\Users\\lenovo\\Desktop\\EcoVision\\Drawing 1.dxf"

# def run_analysis():
#     try: 
#         print("🚀 Sending request to AI Architecture Engine...")
#         with open(file_path, 'rb') as f:
#             files = {'file': f}
#             response = requests.post(URL, files=files)
        
#         if response.status_code == 200:
#             analysis = response.json().get("analysis")
            
#             print("\n" + "="*50)
#             print("🌟 FINAL ARCHITECTURAL REPORT 🌟")
#             print("="*50)
#             print(analysis)
#             print("="*50)
            
#             with open("Architectural_Report.txt", "w", encoding="utf-8") as report_file:
#                 report_file.write(analysis)
#             print("\n💾 Report saved to: Architectural_Report.txt")
            
#         else:
#             print(f"❌ Error {response.status_code}: {response.text}")

#     except Exception as e:
#         print(f"❌ Failed to connect: {e}")

# if __name__ == "__main__":
#     run_analysis()