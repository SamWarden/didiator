========
Didiator
========

``didiator`` is an asynchronous library that implements the Mediator pattern and
uses the `DI <https://www.adriangb.com/di/>`_ library to help you to inject dependencies to called handlers

This library is inspired by the `MediatR <https://github.com/jbogard/MediatR>`_ used in C#,
follows CQRS principles and implements event publishing

Installation
============

Didiator is available on pypi: https://pypi.org/project/didiator

.. code-block:: bash

    pip install -U "didiator[di]"

It will install ``didiator`` with its optional DI dependency that is necessary to use ``DiMiddleware`` and ``DiBuilderImpl``

Examples
========

You can find more examples in `this folder <https://github.com/SamWarden/didiator/tree/dev/examples>`_

Create Commands and Queries with handlers for them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class CreateUser(Command[int]):
        user_id: int
        username: str

    class CreateUserHandler(CommandHandler[CreateUser, int]):
        def __init__(self, user_repo: UserRepo) -> None:
            self._user_repo = user_repo

        async def __call__(self, command: CreateUser) -> int:
            user = User(id=command.user_id, username=command.username)
            await self._user_repo.add_user(user)
            await self._user_repo.commit()
            return user.id

You can use functions as handlers

.. code-block:: python

    @dataclass
    class GetUserById(Query[User]):
        user_id: int

    async def handle_get_user_by_id(query: GetUserById, user_repo: UserRepo) -> User:
        user = await user_repo.get_user_by_id(query.user_id)
        return user

Create DiBuilder
~~~~~~~~~~~~~~~~

``DiBuilderImpl`` is a facade for Container from DI with caching of `solving <https://www.adriangb.com/di/0.73.0/solving/>`_

``di_scopes`` is a list with the order of `scopes <https://www.adriangb.com/di/0.73.0/scopes/>`_

``di_builder.bind(...)`` will `bind <https://www.adriangb.com/di/0.73.0/binds/>`_ ``UserRepoImpl`` type to ``UserRepo`` protocol

.. code-block:: python

    di_scopes = ["request"]
    di_builder = DiBuilderImpl(Container(), AsyncExecutor(), di_scopes)
    di_builder.bind(bind_by_type(Dependent(UserRepoImpl, scope="request"), UserRepo))

Create Mediator
~~~~~~~~~~~~~~~

Create dispatchers with their middlewares and use them to initialize the ``MediatorImpl``

``cls_scope`` is a scope that will be used to bind class Command/Query handlers initialized during request handling

.. code-block:: python

    middlewares = (LoggingMiddleware(), DiMiddleware(di_builder, scopes=DiScopes("request")))
    command_dispatcher = CommandDispatcherImpl(middlewares=middlewares)
    query_dispatcher = QueryDispatcherImpl(middlewares=middlewares)

    mediator = MediatorImpl(command_dispatcher, query_dispatcher)

Register handlers
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # CreateUserHandler is not initialized during registration
    mediator.register_command_handler(CreateUser, CreateUserHandler)
    mediator.register_query_handler(GetUserById, handle_get_user_by_id)

Main usage
~~~~~~~~~~

Enter the ``"request"`` scope that was registered earlier and create a new Mediator with ``di_state`` bound

Use ``mediator.send(...)`` for commands and ``mediator.query(...)`` for queries

.. code-block:: python

        async with di_builder.enter_scope("request") as di_state:
            scoped_mediator = mediator.bind(di_state=di_state)

            # It will call CreateUserHandler(UserRepoImpl()).__call__(command)
            # UserRepoImpl() created and injected automatically
            user_id = await scoped_mediator.send(CreateUser(1, "Jon"))

            # It will call handle_get_user_by_id(query, user_repo)
            # UserRepoImpl created earlier will be reused in this scope
            user = await scoped_mediator.query(GetUserById(user_id))
            print("User:",  user)
        # Session of UserRepoImpl will be closed after exiting the "request" scope

Events publishing
~~~~~~~~~~~~~~~~~

You can register and publish events using ``Mediator`` and its ``EventObserver``.
Unlike dispatchers, ``EventObserver`` publishes events to multiple event handlers subscribed to it
and doesn't return their result.
All middlewares also work with ``EventObserver``, as in in the case with Dispatchers.

Define event and its handlers
-----------------------------

.. code-block:: python

    class UserCreated(Event):
        user_id: int
        username: str

    async def on_user_created1(event: UserCreated, logger: Logger) -> None:
        logger.info("User created1: id=%s,  username=%s", event.user_id, event.username)

    async def on_user_created2(event: UserCreated, logger: Logger) -> None:
        logger.info("User created2: id=%s,  username=%s", event.user_id, event.username)

Create EventObserver and use it for Mediator
--------------------------------------------

.. code-block:: python

    middlewares = (LoggingMiddleware(), DiMiddleware(di_builder, scopes=DiScopes("request")))
    event_observer = EventObserver(middlewares=middlewares)

    mediator = MediatorImpl(command_dispatcher, query_dispatcher, event_observer)

Register event handlers
-----------------------

You can register multiple event handlers for one event

.. code-block:: python

    mediator.register_event_handler(UserCreated, on_user_created1)
    mediator.register_event_handler(UserCreated, on_user_created2)

Publish event
-------------

Event handlers will be executed sequentially

.. code-block:: python

    await mediator.publish(UserCreated(1, "Jon"))
    # User created1: id=1,  username="Jon"
    # User created2: id=1,  username="Jon"

    await mediator.publish([UserCreated(2, "Sam"), UserCreated(3, "Nick")])
    # User created1: id=2,  username="Sam"
    # User created2: id=2,  username="Sam"
    # User created1: id=3,  username="Nick"
    # User created2: id=3,  username="Nick"

⚠️ **Attention: this is a beta version of** ``didiator`` **that depends on** ``DI``, **which is also in beta. Both of them can change their API!**

CQRS
====

CQRS stands for "`Command Query Responsibility Segregation <https://www.martinfowler.com/bliki/CQRS.html>`_".
Its idea about splitting the responsibility of commands (writing) and queries (reading) into different models.

``didiator`` have segregated ``.send(command)``, ``.query(query)`` and ``.publish(events)`` methods in its ``Mediator`` and
assumes that you will separate its handlers.
Use ``CommandMediator``, ``QueryMediator`` and ``EventMediator`` protocols to explicitly define which method you need in ``YourController``

.. code-block:: mermaid

    graph LR;
        YourController-- Query -->Mediator;
        YourController-- Command -->Mediator;
        Mediator-. Query .->QueryDispatcher-.->di2[DiMiddleware]-.->QueryHandler;
        Mediator-. Command .->CommandDispatcher-.->di1[DiMiddleware]-.->CommandHandler;
        CommandHandler-- Event -->Mediator;
        Mediator-. Event .->EventObserver-.->di3[DiMiddleware]-.->EventHandler1;
        EventObserver-.->di4[DiMiddleware]-.->EventHandler2;

``DiMiddleware`` initializes handlers and injects dependencies for them, you can just send a command with the data you need

Why ``didiator``?
=================

- Easy dependency injection to your business logic
- Separating dependencies from your controllers. They can just parse external requests and interact with the ``Mediator``
- CQRS
- Event publishing
- Flexible configuration
- Middlewares support

Why not?
========

- You don't need it
- Maybe too low coupling: navigation becomes more difficult
- Didiator is in beta now
- No support for synchronous handlers

