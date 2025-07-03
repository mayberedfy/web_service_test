FROM python:3.13-slim

WORKDIR /app

# 只复制依赖声明文件，加快缓存
COPY pyproject.toml .
COPY README.md .
COPY src ./src
COPY start.sh .

# 安装构建系统
RUN pip install --upgrade pip && pip install hatchling

# 安装项目依赖（hatchling会读取pyproject.toml）
RUN pip install .


EXPOSE 8000

# 切记：环境变量文件（.env）请不要COPY到镜像，
#       应由服务器在docker run时用 --env-file 注入
CMD ["bash", "start.sh"]