# Refactor This Skill

리팩토링 스킬 - Backend는 Unix Philosophy, Frontend는 추상화 및 중복 제거

## 트리거
- 슬래시 커맨드: `/refactor-this`
- 자연어: "리팩토링해줘", "코드 정리해줘", "refactor"

---

## Backend 리팩토링 (Unix Philosophy)

### 핵심 원칙

**DOTADIW (Do One Thing And Do It Well)**
- 각 함수/클래스는 한 가지 일만 수행
- 함수 이름만 보고 무슨 일을 하는지 알 수 있어야 함

### 리팩토링 체크리스트

```
[ ] 하나의 함수가 여러 가지 일을 하고 있는가? → 분리
[ ] 함수가 20줄을 초과하는가? → 분리 고려
[ ] 비즈니스 로직과 인프라 코드가 섞여 있는가? → 분리
[ ] 중복 코드가 있는가? → 공통 함수로 추출
[ ] 테스트하기 어려운 구조인가? → 의존성 주입 적용
```

### 분리 기준

| 현재 상태 | 리팩토링 방향 |
|----------|--------------|
| 여러 일을 하는 함수 | 단일 책임 함수로 분리 |
| 긴 함수 (20줄+) | 작은 함수들로 분리 |
| 중첩된 조건문 | Early return 패턴 적용 |
| 하드코딩된 값 | 상수/환경변수로 분리 |
| 직접 의존성 | 의존성 주입 패턴 적용 |

### 모듈 구조

```
backend/app/
├── api/           # API 라우터 (정책 - 무엇을 할지)
├── services/      # 비즈니스 로직 (정책 - 어떻게 할지)
├── repositories/  # 데이터 접근 (메커니즘)
├── models/        # 데이터 모델 (표현)
├── schemas/       # Pydantic 스키마 (검증)
└── utils/         # 유틸리티 (메커니즘)
```

### 리팩토링 예시

**Before (여러 가지 일을 하는 함수):**
```python
def process_order(order_data):
    # 유효성 검사
    if not order_data.get('items'):
        raise ValueError("No items")
    # 가격 계산
    total = sum(item['price'] * item['qty'] for item in order_data['items'])
    # 할인 적용
    if order_data.get('coupon'):
        total *= 0.9
    # DB 저장
    db.save(order_data)
    # 이메일 발송
    send_email(order_data['email'], f"주문 완료: {total}원")
    return total
```

**After (각각 한 가지 일만 하는 함수):**
```python
def validate_order(order_data: dict) -> None:
    if not order_data.get('items'):
        raise ValueError("No items")

def calculate_total(items: list) -> int:
    return sum(item['price'] * item['qty'] for item in items)

def apply_discount(total: int, coupon: str | None) -> int:
    if coupon:
        return int(total * 0.9)
    return total

def save_order(order_data: dict) -> Order:
    return order_repository.save(order_data)

def notify_customer(email: str, total: int) -> None:
    notification_service.send_email(email, f"주문 완료: {total}원")
```

---

## Frontend 리팩토링 (추상화 및 중복 제거)

### 핵심 원칙

**DRY (Don't Repeat Yourself)**
- 중복 코드를 공통 컴포넌트/훅으로 추출
- 재사용 가능한 추상화 레이어 구축

### 리팩토링 체크리스트

```
[ ] 비슷한 컴포넌트가 2개 이상 있는가? → 공통 컴포넌트로 추출
[ ] 비슷한 로직이 여러 곳에 있는가? → 커스텀 훅으로 추출
[ ] API 호출 코드가 중복되는가? → API 서비스 레이어 생성
[ ] 스타일이 중복되는가? → 공통 스타일/컴포넌트 생성
[ ] Props가 5개 이상인가? → 객체로 묶거나 컴포넌트 분리
```

### 추상화 레벨

```
frontend/src/
├── components/
│   ├── common/        # 공통 UI 컴포넌트 (Button, Input, Card)
│   ├── layout/        # 레이아웃 컴포넌트 (Header, Sidebar)
│   └── features/      # 기능별 컴포넌트
├── hooks/
│   ├── useApi.ts      # API 호출 훅
│   ├── useForm.ts     # 폼 관리 훅
│   └── useAuth.ts     # 인증 훅
├── services/
│   └── api/           # API 서비스 레이어
├── utils/             # 유틸리티 함수
└── types/             # TypeScript 타입 정의
```

### 리팩토링 예시

**Before (중복된 API 호출):**
```tsx
// UserList.tsx
const [users, setUsers] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

useEffect(() => {
  setLoading(true);
  fetch('/api/users')
    .then(res => res.json())
    .then(data => setUsers(data))
    .catch(err => setError(err))
    .finally(() => setLoading(false));
}, []);

// ProductList.tsx (거의 동일한 코드)
const [products, setProducts] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
// ...
```

**After (커스텀 훅으로 추출):**
```tsx
// hooks/useApi.ts
function useApi<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);

  return { data, loading, error };
}

// UserList.tsx
const { data: users, loading, error } = useApi<User[]>('/api/users');

// ProductList.tsx
const { data: products, loading, error } = useApi<Product[]>('/api/products');
```

**Before (중복된 버튼 스타일):**
```tsx
// 여러 파일에서 반복
<button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  저장
</button>
```

**After (공통 컴포넌트):**
```tsx
// components/common/Button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  children: React.ReactNode;
  onClick?: () => void;
}

export function Button({ variant = 'primary', children, onClick }: ButtonProps) {
  const styles = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  };

  return (
    <button
      className={`px-4 py-2 rounded ${styles[variant]}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

// 사용
<Button variant="primary">저장</Button>
```

---

## 리팩토링 워크플로우

1. **분석**: 현재 코드 구조 파악
2. **식별**: 중복/복잡한 코드 식별
3. **계획**: 리팩토링 범위 결정 (사용자 확인)
4. **테스트 확인**: 기존 테스트 통과 확인
5. **리팩토링**: 단계적으로 수행
6. **테스트 재실행**: 리팩토링 후 테스트 통과 확인
7. **커밋**: 변경사항 커밋

---

## 주의사항

- **기능 변경 금지**: 리팩토링은 동작을 변경하지 않음
- **단계적 진행**: 한 번에 너무 많이 변경하지 않음
- **테스트 필수**: 리팩토링 전후 테스트 통과 확인
- **사용자 확인**: 대규모 구조 변경 시 사용자에게 확인
