import streamlit as st
import os
from dotenv import load_dotenv
from agent import Registry, SingleAgent
from tools import rag_tool_factory, weather_tool_factory, db_tool_factory, employee_tool_factory, list_employees_tool_factory, delete_employee_tool_factory, update_employee_tool_factory, find_employee_tool_factory, delete_employee_by_name_tool_factory, update_employee_by_name_tool_factory

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Single Agent Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #1f77b4;
    }
    .agent-message {
        background-color: #e8f4fd;
        border-left-color: #ff6b6b;
    }
    .tool-info {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_agent():
    """Initialize the agent with tools"""
    reg = Registry()
    reg.register(rag_tool_factory())
    reg.register(weather_tool_factory(os.getenv("WEATHER_API_BASE", "https://api.open-meteo.com/v1/forecast")))
    reg.register(db_tool_factory("data.db"))
    reg.register(employee_tool_factory("data.db"))
    reg.register(list_employees_tool_factory("data.db"))
    reg.register(delete_employee_tool_factory("data.db"))
    reg.register(update_employee_tool_factory("data.db"))
    reg.register(find_employee_tool_factory("data.db"))
    reg.register(delete_employee_by_name_tool_factory("data.db"))
    reg.register(update_employee_by_name_tool_factory("data.db"))
    return SingleAgent(reg)

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Single Agent Demo</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Available Tools")
        
        st.subheader("🔍 RAG Search")
        st.write("Search internal knowledge base using BM25")
        st.code("Example: 'Single Agent hoạt động thế nào?'")
        
        st.subheader("🌤️ Weather API")
        st.write("Get weather for Vietnamese cities")
        st.code("Example: 'Thời tiết ở Hà Nội'")
        
        st.subheader("🗄️ Database")
        st.write("Query customer database (read-only)")
        st.code("Example: 'Tổng số khách hàng'")
        
        st.subheader("👥 Employee Management")
        st.write("**Add:** 'Thêm nhân viên Nguyễn Văn A sinh năm 1990'")
        st.write("**List:** 'Danh sách nhân viên'")
        st.write("**Delete by ID:** 'Xóa nhân viên ID 1'")
        st.write("**Delete by name:** 'Xóa nhân viên Phạm Văn C'")
        st.write("**Update by ID:** 'Sửa nhân viên ID 2 thành Nguyễn Văn C sinh năm 1993'")
        st.write("**Update by name:** 'Sửa nhân viên Lê Quốc An thành sinh năm 2002'")
        st.write("**Find:** 'Tìm nhân viên Lê'")
        
        st.divider()
        
        # Environment info
        st.subheader("⚙️ Configuration")
        use_openai = bool(os.getenv("OPENAI_API_KEY"))
        if use_openai:
            st.success("✅ OpenAI Function Calling Enabled")
            st.write(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
        else:
            st.error("❌ OpenAI API Key Required")
            st.write("**Agent này yêu cầu OpenAI API Key để hoạt động:**")
            st.code("""
# Tạo file .env trong thư mục dự án
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
            """)
            st.write("Không có API key, agent sẽ không thể hiểu và xử lý các yêu cầu tự nhiên.")
    
    # Initialize agent
    agent = initialize_agent()
    
    # Chat interface
    st.subheader("💬 Chat with Agent")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about weather, customers, or knowledge..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = agent.plan_and_act(prompt)
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Example questions
    st.subheader("💡 Example Questions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌤️ Weather**")
        if st.button("Thời tiết ở Đà Nẵng"):
            st.session_state.messages.append({"role": "user", "content": "Thời tiết ở Đà Nẵng"})
            st.rerun()
        if st.button("Weather in Hanoi"):
            st.session_state.messages.append({"role": "user", "content": "Weather in Hanoi"})
            st.rerun()
    
    with col2:
        st.markdown("**🗄️ Database**")
        if st.button("Tổng số khách hàng"):
            st.session_state.messages.append({"role": "user", "content": "Tổng số khách hàng"})
            st.rerun()
        if st.button("How many customers?"):
            st.session_state.messages.append({"role": "user", "content": "How many customers?"})
            st.rerun()
        if st.button("Danh sách nhân viên"):
            st.session_state.messages.append({"role": "user", "content": "Hiển thị danh sách nhân viên"})
            st.rerun()
        if st.button("Thêm nhân viên"):
            st.session_state.messages.append({"role": "user", "content": "Thêm nhân viên Nguyễn Văn A sinh năm 1990"})
            st.rerun()
        if st.button("Xóa theo tên"):
            st.session_state.messages.append({"role": "user", "content": "Xóa nhân viên Phạm Văn C"})
            st.rerun()
        if st.button("Sửa theo tên"):
            st.session_state.messages.append({"role": "user", "content": "Sửa nhân viên Lê Quốc An thành sinh năm 2002"})
            st.rerun()
        if st.button("Tìm nhân viên"):
            st.session_state.messages.append({"role": "user", "content": "Tìm nhân viên Lê"})
            st.rerun()
    
    with col3:
        st.markdown("**🔍 Knowledge**")
        if st.button("Single Agent là gì?"):
            st.session_state.messages.append({"role": "user", "content": "Single Agent là gì?"})
            st.rerun()
        if st.button("How does RAG work?"):
            st.session_state.messages.append({"role": "user", "content": "How does RAG work?"})
            st.rerun()
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Data", type="secondary"):
            # Force refresh by clearing any potential caches
            st.cache_data.clear()
            st.rerun()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        Built with Streamlit • Single Agent Architecture Demo
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
