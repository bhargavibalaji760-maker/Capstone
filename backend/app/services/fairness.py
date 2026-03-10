import numpy as np

def demographic_parity(df, group, pred):
    return df.groupby(group)[pred].mean().to_dict()

def disparate_impact(df, group, pred, priv, unpriv):
    rates = df.groupby(group)[pred].mean()
    return float(rates.get(unpriv,0) / max(rates.get(priv,1e-6),1e-6))

def equal_opportunity(df, group, y_true, y_pred):
    result={}
    for g in df[group].unique():
        sub=df[df[group]==g]
        tp=((sub[y_true]==1)&(sub[y_pred]==1)).sum()
        fn=((sub[y_true]==1)&(sub[y_pred]==0)).sum()
        result[g]=float(tp/(tp+fn+1e-6))
    return result