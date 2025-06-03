#!/bin/bash

APP_NAME="PakapakaApp"
PY_FILE="pakapaka_type1.py"
SPEC_FILE="${APP_NAME}.spec"

echo "🛠️ Cleaning previous builds..."
rm -rf build/ dist/ __pycache__/ "$SPEC_FILE"

echo "📝 Generating spec file..."
pyi-makespec \
  --windowed \
  --name "$APP_NAME" \
  --add-data "sound:MacOS/sound" \
  --add-data "pose_landmarker_lite.task:MacOS/" \
  "$PY_FILE"

echo "🔧 Inserting camera permission into spec file..."
# Add NSCameraUsageDescription to the end of the spec
cat <<EOF >> "$SPEC_FILE"

app = BUNDLE(
    exe,
    name='$APP_NAME.app',
    bundle_identifier='com.example.$APP_NAME',
    info_plist={
        'NSCameraUsageDescription': '이 앱은 자세 추적을 위해 카메라 접근이 필요합니다.',
    },
)
EOF

echo "📦 Building .app with PyInstaller..."
pyinstaller "$SPEC_FILE" --clean

echo "🧹 Removing macOS quarantine flag..."
xattr -cr "dist/${APP_NAME}.app"

echo "📁 Creating zip package..."
cd dist || exit
zip -r "${APP_NAME}.zip" "${APP_NAME}.app"
cd ..

echo "✅ Done! Final file: dist/${APP_NAME}.zip"
