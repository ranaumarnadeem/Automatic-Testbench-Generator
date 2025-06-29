module fsm_example (
    input clk,
    input rst,
    input in,
    output reg [1:0] state
);
    parameter IDLE = 2'b00, S1 = 2'b01, S2 = 2'b10;

    always @(posedge clk or posedge rst) begin
        if (rst)
            state <= IDLE;
        else begin
            case (state)
                IDLE: if (in) state <= S1;
                S1:   if (!in) state <= S2;
                S2:   state <= IDLE;
            endcase
        end
    end
endmodule
