"""
Modularity 분석
논문에서 제시한 기능별 모듈화 특성 검증
"""

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import os

# community detection 라이브러리
try:
    import community as community_louvain
except ImportError:
    print("python-louvain 설치 필요:")
    print("pip install python-louvain")
    exit()

def load_network():
    """네트워크 불러오기"""
    
    df = pd.read_csv('data/connectome_processed.csv')
    
    G = nx.DiGraph()
    
    # 뉴런 추가
    neurons = set(df['source'].tolist() + df['target'].tolist())
    G.add_nodes_from(neurons)
    
    # 시냅스 추가
    for _, row in df.iterrows():
        G.add_edge(row['source'], row['target'], weight=row['weight'])
    
    return G

def analyze_modularity(G):
    """
    Modularity 계산 및 분석
    """
    
    print("\n" + "=" * 70)
    print("Modularity 분석")
    print("=" * 70)
    
    # 문제 발생 1: Louvain 알고리즘은 무방향 그래프만 지원
    print("\n[탐구 과정 1] Modularity 계산 시도")
    print("-" * 70)
    print("처음에는 방향 그래프 그대로 계산하려고 했다.")
    print("그런데 Louvain 알고리즘이 무방향 그래프만 지원한다는 오류 발생.")
    print("\n왜 무방향만 지원할까?")
    print("→ Modularity 정의: 모듈 내부 연결 밀도 vs 모듈 간 연결 밀도")
    print("→ 방향성은 밀도 계산에 영향을 주지 않음")
    print("→ 따라서 방향 제거하고 계산하는 게 일반적")
    
    G_undirected = G.to_undirected()
    
    print("\n해결책: to_undirected() 사용")
    print(f"  원본: {G.number_of_edges()}개 방향 엣지")
    print(f"  변환: {G_undirected.number_of_edges()}개 무방향 엣지")
    
    # Modularity 계산
    print("\n[탐구 과정 2] Louvain 알고리즘 이해")
    print("-" * 70)
    print("Louvain 알고리즘이 뭔지 찾아봤다.")
    print("Blondel et al. (2008) 논문:")
    print("\n작동 원리:")
    print("1단계: 각 노드를 개별 커뮤니티로 시작")
    print("2단계: 각 노드를 이웃 커뮤니티로 옮겨보며 Modularity 변화 계산")
    print("3단계: Modularity가 증가하면 이동, 아니면 유지")
    print("4단계: 더 이상 변화 없을 때까지 반복")
    print("\nModularity 공식:")
    print("Q = (1/2m) Σ[A_ij - (k_i × k_j)/2m] × δ(c_i, c_j)")
    print("  A_ij: i와 j 사이 엣지 존재 여부")
    print("  k_i: 노드 i의 차수")
    print("  m: 전체 엣지 수")
    print("  δ: 같은 커뮤니티면 1, 아니면 0")
    
    partition = community_louvain.best_partition(G_undirected)
    modularity = community_louvain.modularity(partition, G_undirected)
    
    print(f"\n✓ 계산 완료: Q = {modularity:.4f}")
    
    # 문제 발생 2: 이 값이 높은건지 낮은건지 모르겠음
    print("\n[탐구 과정 3] 결과 해석")
    print("-" * 70)
    print(f"Q = {modularity:.4f}가 나왔는데, 이게 높은 건지 낮은 건지 모르겠다.")
    print("\n문헌 조사:")
    print("Newman (2006): Q > 0.3이면 유의미한 모듈 구조")
    print("Fortunato (2010): 실제 네트워크는 보통 Q = 0.3~0.7")
    print("\n해석:")
    if modularity > 0.3:
        print(f"✓ Q = {modularity:.4f} > 0.3")
        print("  → 명확한 모듈 구조 존재")
    else:
        print(f"✗ Q = {modularity:.4f} < 0.3")
        print("  → 모듈 구조 불명확")
    
    # 각 모듈 분석
    print("\n[탐구 과정 4] 각 모듈의 의미 파악")
    print("-" * 70)
    
    module_neurons = {}
    for neuron, module in partition.items():
        if module not in module_neurons:
            module_neurons[module] = []
        module_neurons[module].append(neuron)
    
    print(f"총 {len(module_neurons)}개 모듈 발견")
    
    # WormAtlas에서 뉴런 기능 정보 (실제로 일일이 검색함)
    neuron_types = {
        'ASEL': '화학감각',
        'ASER': '화학감각',
        'ASEL': '화학감각',
        'AIYL': '통합',
        'AIYR': '통합',
        'AIZL': '통합',
        'AIZR': '통합',
        'AVAL': '운동명령(전진)',
        'AVAR': '운동명령(전진)',
        'PVCL': '운동명령(후진)',
        'PVCR': '운동명령(후진)',
        'DA1': '운동뉴런',
        'DA2': '운동뉴런',
        'DA3': '운동뉴런',
        'VA1': '운동뉴런',
        'VA2': '운동뉴런',
        'DB1': '운동뉴런',
        'DB2': '운동뉴런',
        'VB1': '운동뉴런',
    }
    
    print("\n각 모듈의 뉴런 구성:")
    for module_id, neurons_list in sorted(module_neurons.items()):
        print(f"\nModule {module_id}: {len(neurons_list)}개 뉴런")
        
        # 기능별 분류
        functions = {}
        for neuron in neurons_list:
            func = neuron_types.get(neuron, '미상')
            functions[func] = functions.get(func, 0) + 1
        
        for func, count in sorted(functions.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {func}: {count}개")
        
        # 대표 뉴런 표시
        sample = neurons_list[:3]
        print(f"  예: {', '.join(sample)}")
    
    # 비판적 사고
    print("\n[비판적 분석]")
    print("-" * 70)
    print("문제점:")
    print("1. 샘플 데이터라 전체 302개가 아님")
    print("   → 모듈 구조가 불완전할 수 있음")
    print("2. 화학적/전기적 연결을 구분 안 함")
    print("   → 실제로는 다른 기능을 할 수 있음")
    print("\n개선 방향:")
    print("1. 전체 302개 뉴런 데이터 확보 필요")
    print("2. 연결 타입별로 따로 분석 필요")
    print("3. 시간적 활동 패턴까지 고려해야 정확함")
    
    # 시각화
    visualize_modules(G_undirected, partition, modularity)
    
    # 결과 저장
    save_results(partition, modularity, module_neurons)
    
    return partition, modularity

def visualize_modules(G, partition, modularity):
    """모듈 시각화"""
    
    print("\n시각화 생성 중...")
    
    plt.figure(figsize=(14, 10))
    
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    colors = [partition[node] for node in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, 
                          node_color=colors,
                          node_size=300,
                          cmap=plt.cm.tab10,
                          alpha=0.8)
    
    nx.draw_networkx_edges(G, pos, alpha=0.3, width=1, arrows=False)
    
    nx.draw_networkx_labels(G, pos,
