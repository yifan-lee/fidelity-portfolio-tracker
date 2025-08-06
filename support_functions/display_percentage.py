def display_percentage(df, colNames: list):
    df_copy = df.copy()
    for col in colNames:
        df_copy[col] = df_copy[col].apply(lambda x: f"{x:.2%}")
    print(df_copy)
    return 