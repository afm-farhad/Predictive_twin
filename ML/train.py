import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

df = pd.read_csv("data/ai4i2020.csv")
features = [
    'Air temperature [K]',
    'Process temperature [K]',
    'Rotational speed [rpm]',
    'Torque [Nm]',
    'Tool wear [min]'
]
new_features = [
    'air_temp',
    'process_temp',
    'rpm',
    'torque',
    'tool_wear'
]
X = df[features]
X.columns =new_features
y = df['Machine failure']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


#Training_the_model

neg = len(y_train[y_train == 0])
pos = len(y_train[y_train == 1])

model = xgb.XGBClassifier(n_estimators=100, scale_pos_weight=neg/pos, random_state=42)
model.fit(X_train, y_train)


y_pred = model.predict(X_test)
#Performance
report = classification_report(y_test, y_pred)
print(report)

with open('ML/report.txt', 'w') as f:
    f.write(report)

cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Normal', 'Failure'],
            yticklabels=['Normal', 'Failure'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix — XGBoost Predictive Maintenance')
plt.savefig('ML/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
with open('ML/model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model saved as model.pkl")
