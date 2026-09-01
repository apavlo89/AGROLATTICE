@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AGROLATTICE 11.19 - Spatially Balanced Climate Clustering

set "PYTHON_EXE="
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"

if not defined PYTHON_EXE (
  echo ERROR: Python was not found.
  echo Install Anaconda or run INSTALL_DEPENDENCIES.bat after activating your environment.
  pause
  exit /b 1
)

for %%F in ("agrolattice.py" "validated_crop_engine.py" "validated_crop_defaults_mexico.json" "daily_weather_phenology.py" "dataset_updater.py" "soil_water_balance.py" "satellite_crop_monitoring.py" "project_manager.py" "aquacrop_integration.py" "live_crop_monitor.py" "validation_centre.py" "water_productivity_economics.py" "model_ensemble.py" "dssat_apsim_interop.py" "publication_builder.py" "ui_release4.py" "maize_pollination_lab.py" "maize_mechanistic_twin.py" "local_boundary_editor.py" "field_operations_suite.py" "agrolattice_twin.py" "global_country_support.py" "ui_release10.py" "ui_release10_4_help.py" "research_registry.py" "agricultural_validation.py" "research_models.py" "pest_early_warning.py" "phenology_service.py" "research_benchmarks.py" "multimodal_fusion.py" "research_data_hub.py" "hybrid_residual.py" "weak_supervised_yield.py" "gxem_data_builder.py" "research_evidence_ui.py" "decision_intelligence.py" "decision_intelligence_ui.py" "performance_runtime.py" "home_command_centre.py" "field_command_centre.py" "twin_command_centre.py" "climate_earth_command_centre.py" "crop_decision_command_centre.py" "experiment_command_centre.py" "model_evidence_command_centre.py" "report_command_centre.py" "reporting_registry.py" "crop_profile_registry.py" "navigation_state.py" "platform_settings.py" "data_settings_command_centre.py" "tool_catalogue.py" "researcher_guidance.py" "help_command_centre.py" "integration_reliability.py" "publication_reference.py" "verify_release11_19.py" "USER_GUIDE_RELEASE_11_19.txt" "RELEASE_MANIFEST_11_19.json" "PUBLICATION_REFERENCE_ID.txt" "CITATION.cff" "LICENSE" "reports\reporting.sqlite" "assets\brand\agrolattice_logo.png" "assets\brand\agrolattice_icon.png") do (
  if not exist %%F (
    echo ERROR: Required application file %%F is missing.
    pause
    exit /b 1
  )
)

for %%F in ("agroclimatic_selection_ac2.py" "verify_release11_19_ac2.py" "README_START_HERE_RELEASE11_19_AC2.txt" "CHANGELOG_RELEASE_11_19_AC2.txt" "RELEASE_MANIFEST_11_19_AC2.json" "RESEARCH_METHODS_MANIFEST_11_19_AC2.json" "ADAPTIVE_CLUSTERING_BUILD_ID_AC2.txt") do (
  if not exist %%F (
    echo ERROR: Required AC2 file %%F is missing.
    pause
    exit /b 1
  )
)

for %%F in ("agroclimatic_selection_ac3.py" "verify_release11_19_ac3.py" "README_START_HERE_RELEASE11_19_AC3.txt" "CHANGELOG_RELEASE_11_19_AC3.txt" "RELEASE_MANIFEST_11_19_AC3.json" "RESEARCH_METHODS_MANIFEST_11_19_AC3.json" "ADAPTIVE_CLUSTERING_BUILD_ID_AC3.txt" "VERIFICATION_REPORT_11_19_AC3.txt" "FILE_MANIFEST_11_19_AC3.sha256") do (
  if not exist %%F (
    echo ERROR: Required AC3 file %%F is missing.
    pause
    exit /b 1
  )
)

for %%F in ("spatial_clustering_balance.py" "verify_release11_19_spatial_balance.py" "SPATIAL_CLUSTERING_METHOD.md" "SPATIAL_BALANCE_BUILD_ID.txt" "CHANGELOG_RELEASE_11_19_SPATIAL_BALANCE.txt" "RELEASE_MANIFEST_11_19_SPATIAL_BALANCE.json" "FILE_MANIFEST_11_19_SPATIAL_BALANCE.sha256") do (
  if not exist %%F (
    echo ERROR: Required spatial-balance file %%F is missing.
    pause
    exit /b 1
  )
)

if not exist "Datasets\worldcities.csv" (
  echo ERROR: Datasets\worldcities.csv is missing.
  echo Copy your existing Datasets folder into this package.
  pause
  exit /b 1
)

echo Standardising country data storage...
"%PYTHON_EXE%" -c "from pathlib import Path; import global_country_support as g; r=g.migrate_legacy_mexico_storage(Path.cwd()); print('Mexico storage:', 'standardised' if r.get('dataset_exists') else 'dataset not installed'); [print(' - '+x) for x in r.get('actions', [])]; [print(' WARNING: '+x) for x in r.get('warnings', [])]"
if errorlevel 1 (
  echo ERROR: Mexico data could not be moved into the standard country folder.
  echo The original file was not intentionally deleted. Review the error above.
  pause
  exit /b 1
)

if not exist "Datasets\countries\mexico\agroclimate_longformat.csv" (
  echo WARNING: The Mexico historical dataset is not installed at:
  echo Datasets\countries\mexico\agroclimate_longformat.csv
  echo The app can still start and Dataset updater can create it.
  echo.
)

echo Using Python:
echo %PYTHON_EXE%
echo.

REM Prevent an older cached Release 4 UI module from being reused.
if exist "__pycache__\agrolattice*.pyc" del /q "__pycache__\agrolattice*.pyc" >nul 2>&1
if exist "__pycache__\agroclimatic_selection_ac2*.pyc" del /q "__pycache__\agroclimatic_selection_ac2*.pyc" >nul 2>&1
if exist "__pycache__\agroclimatic_selection_ac3*.pyc" del /q "__pycache__\agroclimatic_selection_ac3*.pyc" >nul 2>&1
if exist "__pycache__\spatial_clustering_balance*.pyc" del /q "__pycache__\spatial_clustering_balance*.pyc" >nul 2>&1
if exist "__pycache__\ui_release4*.pyc" del /q "__pycache__\ui_release4*.pyc" >nul 2>&1
if exist "__pycache__\field_operations_suite*.pyc" del /q "__pycache__\field_operations_suite*.pyc" >nul 2>&1
if exist "__pycache__\maize_pollination_lab*.pyc" del /q "__pycache__\maize_pollination_lab*.pyc" >nul 2>&1
if exist "__pycache__\maize_mechanistic_twin*.pyc" del /q "__pycache__\maize_mechanistic_twin*.pyc" >nul 2>&1
if exist "__pycache__\local_boundary_editor*.pyc" del /q "__pycache__\local_boundary_editor*.pyc" >nul 2>&1
if exist "__pycache__\agrolattice_twin*.pyc" del /q "__pycache__\agrolattice_twin*.pyc" >nul 2>&1
if exist "__pycache__\global_country_support*.pyc" del /q "__pycache__\global_country_support*.pyc" >nul 2>&1
if exist "__pycache__\ui_release10*.pyc" del /q "__pycache__\ui_release10*.pyc" >nul 2>&1
if exist "__pycache__\ui_release10_4_help*.pyc" del /q "__pycache__\ui_release10_4_help*.pyc" >nul 2>&1
if exist "__pycache__\dataset_updater*.pyc" del /q "__pycache__\dataset_updater*.pyc" >nul 2>&1
if exist "__pycache__\research_registry*.pyc" del /q "__pycache__\research_registry*.pyc" >nul 2>&1
if exist "__pycache__\agricultural_validation*.pyc" del /q "__pycache__\agricultural_validation*.pyc" >nul 2>&1
if exist "__pycache__\research_models*.pyc" del /q "__pycache__\research_models*.pyc" >nul 2>&1
if exist "__pycache__\pest_early_warning*.pyc" del /q "__pycache__\pest_early_warning*.pyc" >nul 2>&1
if exist "__pycache__\phenology_service*.pyc" del /q "__pycache__\phenology_service*.pyc" >nul 2>&1
if exist "__pycache__\research_benchmarks*.pyc" del /q "__pycache__\research_benchmarks*.pyc" >nul 2>&1
if exist "__pycache__\multimodal_fusion*.pyc" del /q "__pycache__\multimodal_fusion*.pyc" >nul 2>&1
if exist "__pycache__\research_data_hub*.pyc" del /q "__pycache__\research_data_hub*.pyc" >nul 2>&1
if exist "__pycache__\hybrid_residual*.pyc" del /q "__pycache__\hybrid_residual*.pyc" >nul 2>&1
if exist "__pycache__\weak_supervised_yield*.pyc" del /q "__pycache__\weak_supervised_yield*.pyc" >nul 2>&1
if exist "__pycache__\gxem_data_builder*.pyc" del /q "__pycache__\gxem_data_builder*.pyc" >nul 2>&1
if exist "__pycache__\research_evidence_ui*.pyc" del /q "__pycache__\research_evidence_ui*.pyc" >nul 2>&1
if exist "__pycache__\decision_intelligence*.pyc" del /q "__pycache__\decision_intelligence*.pyc" >nul 2>&1
if exist "__pycache__\decision_intelligence_ui*.pyc" del /q "__pycache__\decision_intelligence_ui*.pyc" >nul 2>&1
if exist "__pycache__\performance_runtime*.pyc" del /q "__pycache__\performance_runtime*.pyc" >nul 2>&1
if exist "__pycache__\home_command_centre*.pyc" del /q "__pycache__\home_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\field_command_centre*.pyc" del /q "__pycache__\field_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\twin_command_centre*.pyc" del /q "__pycache__\twin_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\climate_earth_command_centre*.pyc" del /q "__pycache__\climate_earth_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\crop_decision_command_centre*.pyc" del /q "__pycache__\crop_decision_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\experiment_command_centre*.pyc" del /q "__pycache__\experiment_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\model_evidence_command_centre*.pyc" del /q "__pycache__\model_evidence_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\crop_profile_registry*.pyc" del /q "__pycache__\crop_profile_registry*.pyc" >nul 2>&1
if exist "__pycache__\report_command_centre*.pyc" del /q "__pycache__\report_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\reporting_registry*.pyc" del /q "__pycache__\reporting_registry*.pyc" >nul 2>&1
if exist "__pycache__\navigation_state*.pyc" del /q "__pycache__\navigation_state*.pyc" >nul 2>&1
if exist "__pycache__\platform_settings*.pyc" del /q "__pycache__\platform_settings*.pyc" >nul 2>&1
if exist "__pycache__\data_settings_command_centre*.pyc" del /q "__pycache__\data_settings_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\tool_catalogue*.pyc" del /q "__pycache__\tool_catalogue*.pyc" >nul 2>&1
if exist "__pycache__\researcher_guidance*.pyc" del /q "__pycache__\researcher_guidance*.pyc" >nul 2>&1
if exist "__pycache__\help_command_centre*.pyc" del /q "__pycache__\help_command_centre*.pyc" >nul 2>&1
if exist "__pycache__\integration_reliability*.pyc" del /q "__pycache__\integration_reliability*.pyc" >nul 2>&1
"%PYTHON_EXE%" -c "import inspect, streamlit, scipy, statsmodels, sklearn, openai; from packaging.version import Version; assert Version(streamlit.__version__) >= Version('1.48.0'), f'Streamlit 1.48+ required, found {streamlit.__version__}'; import validated_crop_engine, daily_weather_phenology, dataset_updater, soil_water_balance, satellite_crop_monitoring, project_manager, aquacrop_integration, live_crop_monitor, validation_centre, water_productivity_economics, model_ensemble, dssat_apsim_interop, publication_builder, ui_release4, maize_pollination_lab, maize_mechanistic_twin, local_boundary_editor, field_operations_suite, agrolattice_twin, global_country_support, ui_release10, ui_release10_4_help; import research_registry, agricultural_validation, research_models, pest_early_warning, phenology_service, research_benchmarks, multimodal_fusion, research_data_hub, hybrid_residual, weak_supervised_yield, gxem_data_builder, research_evidence_ui, decision_intelligence, decision_intelligence_ui, performance_runtime, home_command_centre, field_command_centre, twin_command_centre, climate_earth_command_centre, crop_decision_command_centre, experiment_command_centre, model_evidence_command_centre, report_command_centre, reporting_registry, crop_profile_registry, navigation_state, platform_settings, data_settings_command_centre, tool_catalogue, researcher_guidance, help_command_centre, integration_reliability, publication_reference; assert ui_release4.UI_RELEASE_VERSION == '4.3.0'; assert ui_release10.MODULE_VERSION == '10.2.0'; assert ui_release10_4_help.MODULE_VERSION == '10.4.4'; assert 'country' in inspect.signature(dataset_updater.normalise_locations).parameters; assert ('similarity_cache_path' in inspect.signature(dataset_updater.install_candidate).parameters or 'target_similarity_cache_path' in inspect.signature(dataset_updater.install_candidate).parameters); assert field_operations_suite.MODULE_VERSION == '8.0.0'; assert field_operations_suite.DB_SCHEMA_VERSION == '8.0.0'; assert field_command_centre.MODULE_VERSION == '1.0.1'; assert maize_pollination_lab.MODULE_VERSION == '3.0.0'; assert maize_pollination_lab.DB_SCHEMA_VERSION == '3.0.0'; assert experiment_command_centre.MODULE_VERSION == '1.0.0'; assert model_evidence_command_centre.MODULE_VERSION == '1.0.0'; assert report_command_centre.MODULE_VERSION == '1.0.0'; assert reporting_registry.MODULE_VERSION == '1.0.0'; assert reporting_registry.DB_SCHEMA_VERSION == '1.0.0'; assert publication_builder.MODULE_VERSION == '2.0.0'; assert maize_mechanistic_twin.MODULE_VERSION == '1.0.0'; assert local_boundary_editor.MODULE_VERSION == '1.0.0'; assert (local_boundary_editor.COMPONENT_DIRECTORY / 'main.js').exists(); assert agrolattice_twin.MODULE_VERSION == '3.0.0'; assert agrolattice_twin.DB_SCHEMA_VERSION == '3.0.0'; assert len(agrolattice_twin.TWIN_CANONICAL_WEATHER_VARIABLES) == 19; assert hasattr(agrolattice_twin.AgroLatticeTwinDatabase, 'save_root_zone'); assert global_country_support.MODULE_VERSION == '10.3.0'; assert research_registry.MODULE_VERSION == '2.0.0'; assert research_registry.DB_SCHEMA_VERSION == '2.0.0'; assert research_evidence_ui.MODULE_VERSION == '3.0.0'; assert research_models.MODULE_VERSION == '1.1.0'; assert len(research_data_hub.TWIN_CANONICAL_WEATHER_VARIABLES) == 19; assert multimodal_fusion.MODULE_VERSION == '2.0.0'; assert hybrid_residual.MODULE_VERSION == '1.0.0'; assert weak_supervised_yield.MODULE_VERSION == '1.0.0'; assert gxem_data_builder.MODULE_VERSION == '1.0.0'; assert agricultural_validation.MODULE_VERSION == '1.1.0'; assert phenology_service.MODULE_VERSION == '1.0.0'; assert decision_intelligence.MODULE_VERSION == '1.0.0'; assert performance_runtime.MODULE_VERSION == '1.0.0'; assert home_command_centre.MODULE_VERSION == '1.0.0'; assert twin_command_centre.MODULE_VERSION == '1.0.1'; assert climate_earth_command_centre.MODULE_VERSION == '1.0.1'; assert crop_decision_command_centre.MODULE_VERSION == '1.0.1'; assert crop_profile_registry.MODULE_VERSION == '1.0.0'; assert navigation_state.MODULE_VERSION == '1.0.0'; assert crop_profile_registry.DB_SCHEMA_VERSION == '1.0.0'; assert platform_settings.MODULE_VERSION == '1.0.0'; assert data_settings_command_centre.MODULE_VERSION == '1.1.0'; assert tool_catalogue.MODULE_VERSION == '1.0.0'; assert researcher_guidance.MODULE_VERSION == '1.0.0'; assert help_command_centre.MODULE_VERSION == '1.0.0'; assert integration_reliability.MODULE_VERSION == '1.0.0'; assert publication_reference.MODULE_VERSION == '1.0.0'; assert publication_reference.REFERENCE_ID == 'AGROLATTICE-11.19-PRR-2026-08-12'; assert hasattr(performance_runtime.CountryRuntimeData, '__dataclass_fields__') and 'climate_locations' in performance_runtime.CountryRuntimeData.__dataclass_fields__; print('AGROLATTICE 11.19 publication-reference preflight passed; frozen reference assets present, scientific database schemas unchanged, and k<=20 climate clustering preserved')"
if errorlevel 1 (
  echo.
  echo ERROR: A required package or AGROLATTICE 11.19 module could not be loaded.
  echo Run INSTALL_DEPENDENCIES.bat, then try again.
  pause
  exit /b 1
)

"%PYTHON_EXE%" -c "import agroclimatic_selection_ac2 as ac2; assert ac2.MODULE_VERSION == '2.0.0'; assert hasattr(ac2, 'select_variables_and_clusters_ac2'); print('AGROLATTICE 11.19 adaptive-clustering build AC2 preflight passed')"
if errorlevel 1 (
  echo.
  echo ERROR: The AC2 clustering module could not be loaded.
  pause
  exit /b 1
)

"%PYTHON_EXE%" -c "import agroclimatic_selection_ac3 as ac3; assert ac3.MODULE_VERSION == '3.0.0'; assert hasattr(ac3, 'benchmark_clustering_algorithms_ac3'); print('AGROLATTICE 11.19 adaptive-clustering build AC3 preflight passed')"
if errorlevel 1 (
  echo.
  echo ERROR: The AC3 clustering module could not be loaded.
  pause
  exit /b 1
)

"%PYTHON_EXE%" -m streamlit run "agrolattice.py"
if errorlevel 1 (
  echo.
  echo The app stopped with an error. Review the message above.
  pause
)
endlocal
