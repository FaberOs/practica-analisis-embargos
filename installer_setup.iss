; Script de instalación para DashboardEmbargos
; Requiere Inno Setup Compiler (https://jrsoftware.org/isinfo.php)

#define MyAppName "Dashboard de Embargos Bancarios"
#define MyAppVersion "2.0"
#define MyAppPublisher "Análisis de Embargos"
#define MyAppURL "https://github.com"
#define MyAppExeName "DashboardEmbargos.exe"

[Setup]
; Información básica de la aplicación
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer
OutputBaseFilename=DashboardEmbargos_Installer
SetupIconFile="ob.ico"
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
; NOTA: El ejecutable incluye todas las dependencias de Python (Streamlit, pandas, plotly, sklearn, xgboost, etc.)
; No se requiere Python instalado en el sistema
; El ejecutable es completamente autónomo
; El usuario solo necesita proporcionar el CSV original de la BD (con años en el nombre)
; El modelo procesará los datos automáticamente

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Dirs]
; Crear la carpeta datos para que los usuarios sepan dónde colocar los CSV
Name: "{app}\datos"; Flags: uninsneveruninstall

[Files]
; Incluir el ejecutable principal (obligatorio - siempre incluir)
Source: "dist\DashboardEmbargos.exe"; DestDir: "{app}"; Flags: ignoreversion
; NOTA: Los archivos CSV NO se incluyen en el instalador
; Los usuarios solo necesitan el CSV original de la BD (con años en el nombre, por semestres)
; El modelo procesará automáticamente los datos y generará los archivos necesarios
; Incluir documentación (solo si existe)
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
; Archivos opcionales de documentación (descomentar si existen)
; Source: "INSTRUCCIONES_EJECUTABLE.md"; DestDir: "{app}"; Flags: ignoreversion
; Source: "INSTRUCCIONES_CSV.txt"; DestDir: "{app}\datos"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// La verificación de archivos se hace durante la compilación, no durante la instalación
// Los archivos ya están incluidos en el instalador cuando se compila
function InitializeSetup(): Boolean;
begin
  Result := True;
  // No es necesario verificar aquí, los archivos ya están en el instalador
  // El ejecutable incluye todas las dependencias de Python (Streamlit, pandas, plotly, etc.)
  // No se requiere Python instalado en el sistema
end;

// Función para mostrar información después de la instalación
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // El ejecutable es autónomo y no requiere dependencias adicionales
    // Los archivos CSV se pueden agregar después usando la interfaz gráfica
    // La carpeta datos ya se crea automáticamente mediante [Dirs]
  end;
end;

// Función para mostrar mensaje informativo después de la instalación
procedure CurPageChanged(CurPageID: Integer);
var
  datosPath: String;
begin
  if CurPageID = wpFinished then
  begin
    datosPath := ExpandConstant('{app}\datos');
    MsgBox(
      '¡Instalación completada!' + #13#10 + #13#10 +
      'IMPORTANTE: Para usar el dashboard, necesitas proporcionar el CSV original de la Base de Datos.' + #13#10 + #13#10 +
      'Archivo CSV necesario:' + #13#10 +
      '  - CSV extraído de la BD (con años en el nombre, por semestres)' + #13#10 +
      '    Ejemplo: "consulta detalle embargos-2023-01.csv"' + #13#10 + #13#10 +
      'El modelo procesará automáticamente los datos y generará:' + #13#10 +
      '  - embargos_consolidado_mensual.csv' + #13#10 +
      '  - predicciones_oficios_por_mes.csv' + #13#10 +
      '  - predicciones_demandados_por_mes.csv' + #13#10 +
      '  - resultados_clasificaciones.csv' + #13#10 + #13#10 +
      'Cómo usar:' + #13#10 +
      '  1. Ejecuta DashboardEmbargos.exe' + #13#10 +
      '  2. Selecciona el/los archivo(s) CSV de la BD' + #13#10 +
      '  3. Inicia el dashboard deseado' + #13#10 +
      '  4. El modelo procesará los datos automáticamente' + #13#10 + #13#10 +
      'Los archivos generados se guardarán en:' + #13#10 +
      '  ' + ExpandConstant('{userappdata}') + '\DashboardEmbargos\datos',
      mbInformation, MB_OK
    );
  end;
end;

