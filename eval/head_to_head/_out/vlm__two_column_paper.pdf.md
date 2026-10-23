# Bearing Fault Diagnosis with Combined Features

*A. Rao and S. Iyer*

## 1. Introduction

Condition monitoring of rotating machinery relies on vibration signals. In this study we compare three feature sets on a bearing fault data set. The first feature set uses time domain statistics such as root mean square and kurtosis. The second uses spectral band energies.

## 2. Method and results

The third feature set combines both with envelope analysis. A random forest classifier achieved the best accuracy on the held out test set. Results are summarised in Table 1. We conclude that combined features give the most robust diagnosis across operating speeds.

Table 1. Accuracy by feature set (percent)

| Feature set | Accuracy |
|---------------|----------|
| Time domain | 88.2 |
| Spectral | 91.5 |
| Combined | 96.3 |